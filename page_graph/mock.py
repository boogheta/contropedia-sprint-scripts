''' Just some mock variables to enable developing the client while waiting
for backend to be complete. '''

SAMPLE_GRAPH = {
    'nodes': [
        {
            'id': 'n01',
            'label': 'Node 1',
            'x': 34,
            'y': 45
        },
        {
            'id': 'n02',
            'label': 'Node 2',
            'x': 56,
            'y': 89
        }
    ],
    'edges': [
        {
            'id': 'e01',
            'source': 'n01',
            'target': 'n02',
            'weight': 1
        }
    ]
}

SUPPLEMENTARY_GRAPH = {
    'nodes': [
        {
            'id': 'n03',
            'label': 'Node 3',
            'x': 56,
            'y': 23
        }
    ],
    'edges': [
        {
            'id': 'e03',
            'source': 'n01',
            'target': 'n03',
            'weight': 1
        }
    ]
}
