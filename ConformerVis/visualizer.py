import os
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import rdMolAlign
from vedo import Plotter, Sphere, Text2D, Line, Text3D
import constants  # Import your constants.py where vconf_batch_sdf_path is defined

# Load conformers from the SDF file specified in constants.py
sdf_path = constants.vconf_batch_sdf_path
if not os.path.exists(sdf_path):
    raise FileNotFoundError(f"File not found: {sdf_path}")

# Load the molecules from the SDF file
suppl = Chem.SDMolSupplier(sdf_path, removeHs=False, sanitize=False)
conformers = [mol for mol in suppl if mol is not None]

if not conformers:
    raise ValueError("No valid molecules found in the SDF file.")

# Function to get atomic radius based on element
def get_atomic_radius(elem):
    atomic_radii = {
        'H': 1.0,  # Hydrogen
        'C': 1.4166,  # Carbon
        'N': 1.2916,  # Nitrogen
        'O': 1.2666,  # Oxygen
        'F': 1.2250,  # Fluorine
        'S': 1.5000,  # Sulfur
    }
    return atomic_radii.get(elem, 1.0)  # Default radius for unknown elements

# Function to draw atoms and bonds based on the current view mode
def draw_molecule_with_labels(mol, plotter, view_mode):
    # Get the atom positions and types
    conformer = mol.GetConformer(0)
    positions = conformer.GetPositions()

    # Draw atoms and bonds based on view mode
    for i, atom in enumerate(mol.GetAtoms()):
        pos = positions[i]
        elem = atom.GetSymbol()

        # Get the atom radius based on element type
        radius = get_atomic_radius(elem)
        transparency = 0.25 if elem == 'F' else 1.0  # Fluorine is semi-transparent

        # Define color for each atom type
        color = {
            'C': "gray",
            'O': "red",
            'F': "green",
            'S': "yellow",
            'H': "white"
        }.get(elem, "blue")  # fallback for unknown elements

        # Handle the different view modes
        if view_mode == 1:
            # Mode 1: Only show stick-bonds (no spheres)
            pass  # No spheres in this mode, just bonds below
        elif view_mode == 2:
            # Mode 2: Hide fluorines and hydrogens, show other atoms with default sphere size
            if elem not in ['F', 'H']:
                atom_sphere = Sphere(pos, r=0.5).c(color)
                plotter += atom_sphere
        else:
            # Mode 3: Show full van-der Waals spheres
            atom_sphere = Sphere(pos, r=radius).c(color).alpha(transparency)
            plotter += atom_sphere

        # Draw the label on the atom (letter inside the sphere), only if spheres are shown
        if view_mode != 1 and elem not in ['F', 'H']:
            label = Text3D(elem, pos, s=0.3, c="black", justify="center")
            plotter += label

    # Draw bonds for all modes (except Mode 2 when bonds involve fluorine or hydrogen)
    for bond in mol.GetBonds():
        start_idx = bond.GetBeginAtomIdx()
        end_idx = bond.GetEndAtomIdx()

        start_atom = mol.GetAtomWithIdx(start_idx)
        end_atom = mol.GetAtomWithIdx(end_idx)

        start_elem = start_atom.GetSymbol()
        end_elem = end_atom.GetSymbol()

        # In Mode 2, skip bonds involving fluorine or hydrogen
        if view_mode == 2 and (start_elem in ['F', 'H'] or end_elem in ['F', 'H']):
            continue  # Skip drawing this bond

        start_pos = positions[start_idx]
        end_pos = positions[end_idx]

        bond_line = Line(start_pos, end_pos).c("black").lw(3)  # lw: line width
        plotter += bond_line


# Extract molecule name from the SDF block
def get_molecule_name(mol):
    name = mol.GetProp("_Name") if mol.HasProp("_Name") else "Unknown"
    return name

# Align conformers to minimize distances (using RMSD) relative to the previous conformer, ignoring fluorine atoms
def align_conformer_to_previous(ref_mol, target_mol):
    # Create an atom map, excluding fluorine atoms from alignment
    atom_map = []
    for i, atom in enumerate(ref_mol.GetAtoms()):
        if atom.GetSymbol() != 'F':  # Ignore fluorine atoms
            atom_map.append((i, i))

    # Align the target molecule to the reference molecule using the atom map
    rdMolAlign.AlignMol(target_mol, ref_mol, atomMap=atom_map)

# Function to extract energy from the SDF data
def get_energy(mol):
    energy = mol.GetProp("Energy") if mol.HasProp("Energy") else "Unknown Energy"
    return energy

# Class for managing conformer visualization
class ConformerViewer:
    def __init__(self, conformers):
        self.conformers = conformers
        self.current_conformer_index = 0
        self.view_mode = 3  # Start in full van-der Waals mode

        # Perform RMSD alignment for all conformers relative to the previous one, ignoring fluorine atoms
        self.align_all_conformers()

        # Create the Vedo plotter
        self.plotter = Plotter(size=(800, 600), interactive=True)
        self.update_conformer()

        # Add keypress callback for navigation
        self.plotter.add_callback('KeyPress', self.keypress)

        self.plotter.show(interactive=True)

    # Visualize the current conformer using Vedo
    def update_conformer(self):
        mol = self.conformers[self.current_conformer_index]

        # Clear previous conformer visualization
        self.plotter.clear()

        # Draw current molecule with atom labels and bonds
        draw_molecule_with_labels(mol, self.plotter, self.view_mode)

        # Get molecule name and energy and update the title
        molecule_name = get_molecule_name(mol)
        energy = get_energy(mol)
        title = f'Molecule: {molecule_name}, Energy: {energy} kcal/mol'

        # Update the window title
        self.plotter.render()  # Ensure rendering occurs
        self.plotter.window.SetWindowName(title)  # Update the window name dynamically

        # Render the updated scene
        self.plotter.render()

    # Handle keypresses for navigation and toggling
    def keypress(self, evt):
        if evt.keypress == 'Right':
            self.show_next_conformer()
        elif evt.keypress == 'Left':
            self.show_previous_conformer()
        elif evt.keypress == 'Down':
            self.toggle_view_mode()

    # Toggle between different viewing modes when down arrow is pressed
    def toggle_view_mode(self):
        self.view_mode = (self.view_mode % 3) + 1  # Cycle between 1, 2, and 3
        self.update_conformer()  # Redraw the current conformer with the new view mode

    # Show the previous conformer
    def show_previous_conformer(self):
        if self.current_conformer_index > 0:
            self.current_conformer_index -= 1
            self.update_conformer()

    # Show the next conformer
    def show_next_conformer(self):
        if self.current_conformer_index < len(self.conformers) - 1:
            self.current_conformer_index += 1
            self.update_conformer()

    # Align all conformers to the previous one, ignoring fluorine atoms
    def align_all_conformers(self):
        ref_mol = self.conformers[0]  # Use the first conformer as the reference
        for i in range(1, len(self.conformers)):
            align_conformer_to_previous(ref_mol, self.conformers[i])
            ref_mol = self.conformers[i]  # Set the current as the new reference for the next

# Main function to run the application
if __name__ == "__main__":
    viewer = ConformerViewer(conformers)
