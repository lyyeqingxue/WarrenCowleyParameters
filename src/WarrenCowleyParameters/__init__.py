import numpy as np
from ovito.data import (
    DataCollection,
    DataTable,
    ElementType,
    NearestNeighborFinder,
    ParticleType,
)
from ovito.pipeline import ModifierInterface
from traits.api import ListInt


class WarrenCowleyParameters(ModifierInterface):
    nneigh = ListInt([0, 12], label="Max atoms in shells", minlen=1)

    def get_concentration(self, particle_types):
        unique_types, counts = np.unique(particle_types, return_counts=True)
        return unique_types, counts / len(particle_types)

    def get_central_atom_type_mask(self, unique_types, particles_types):
        central_atom_type_mask = []
        for atom_type in unique_types:
            central_atom_type_mask.append(np.where(particles_types == atom_type))
        return central_atom_type_mask

    def get_wc_from_neigh_in_shell_types(
        self, neigh_in_shell_types, central_atom_type_mask, c, unique_types
    ):
        ntypes = len(c)
        wc = np.zeros((ntypes, ntypes))

        for i in range(ntypes):
            neight_type_aroud_itype = neigh_in_shell_types[central_atom_type_mask[i]].flatten()
            counts = np.bincount(neight_type_aroud_itype)
            pij = counts[unique_types] / len(neight_type_aroud_itype)
            wc[i, :] = 1 - pij / c

        # for i in range(ntypes):
        #     neight_type_aroud_itype = neigh_in_shell_types[central_atom_type_mask[i]].flatten()
        #     for j in range(ntypes):
        #         # pij is the average probability of finding a j-type atom around an i-type atom in the mth shell
        #         pij = len(
        #             neight_type_aroud_itype[neight_type_aroud_itype == unique_types[j]]
        #         ) / len(neight_type_aroud_itype)

        #         wc[i, j] = 1 - pij / c[j]

        return wc

    def modify(self, data: DataCollection, frame: int, **kwargs):
        particles_types = np.array(data.particles.particle_type)
        ntypes = len(np.unique(particles_types))

        max_number_of_neigh = np.max(self.nneigh)
        finder = NearestNeighborFinder(max_number_of_neigh, data)
        neigh_idx, _ = finder.find_all()

        unique_types, c = self.get_concentration(particles_types)
        central_atom_type_mask = self.get_central_atom_type_mask(unique_types, particles_types)

        nshells = len(self.nneigh) - 1
        wc_for_shells = np.zeros((nshells, ntypes, ntypes))

        for m in range(nshells):
            neigh_idx_in_shell = neigh_idx[:, self.nneigh[m] : self.nneigh[m + 1]]
            neigh_in_shell_types = particles_types[neigh_idx_in_shell]

            wc = self.get_wc_from_neigh_in_shell_types(
                neigh_in_shell_types, central_atom_type_mask, c, unique_types
            )
            wc_for_shells[m] = wc
        breakpoint()
