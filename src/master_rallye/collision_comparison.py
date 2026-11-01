"""Parser-only collision comparisons shared with the existing RDemo research.

Extracted from its collision_oracle_analysis pure comparison helpers, avoiding
the optional GXM/original-cooker oracle dependency in ordinary DX comparison.
Secondary descriptor order is reported and never relabelled as core topology.
"""
from collections import Counter


def compare_secondary_descriptors(first_faces, second_faces):
    changed=[];permutations=[];multisets=len(first_faces)==len(second_faces)
    for index in range(max(len(first_faces),len(second_faces))):
        first=tuple(first_faces[index].secondary_indices)if index<len(first_faces)else None
        second=tuple(second_faces[index].secondary_indices)if index<len(second_faces)else None
        same=first is not None and second is not None and Counter(first)==Counter(second)
        if not same:multisets=False
        if first!=second:
            changed.append({'face_index':index,'first':list(first)if first is not None else None,
                            'second':list(second)if second is not None else None,'per_face_multiset_equal':same})
            if same:permutations.append(index)
    exact=len(first_faces)==len(second_faces)and not changed
    return {'classification':'AUXILIARY_SECONDARY_DESCRIPTORS_EQUAL'if exact else'AUXILIARY_SECONDARY_DESCRIPTORS_DIFFER',
            'semantics':'UNRESOLVED','exact_tuples_equal':exact,'per_face_multisets_equal':multisets,
            'changed_face_count':len(changed),'pure_permutation_face_indices':permutations,'changed_faces':changed}


def compare_core_topology(first,second):
    checks={'vertex_count_equal':first.geometry_a.vertex_count==second.geometry_a.vertex_count,
            'triangle_count_equal':first.geometry_a.triangle_count==second.geometry_a.triangle_count,
            'triangle_indices_equal':first.geometry_a.triangles==second.geometry_a.triangles,
            'referenced_vertex_indices_equal':first.referenced_vertex_indices==second.referenced_vertex_indices,
            'edges_equal':first.edges==second.edges,
            'primary_descriptors_equal':tuple(f.primary_indices for f in first.face_descriptors)==tuple(f.primary_indices for f in second.face_descriptors),
            'edge_face_adjacency_equal':first.edge_face_adjacency==second.edge_face_adjacency,
            'face_loops_equal':first.face_loop_indices==second.face_loop_indices}
    return {'classification':'CORE_TOPOLOGY_EQUAL'if all(checks.values())else'CORE_TOPOLOGY_DIFFERENT','checks':checks}
