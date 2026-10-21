def alan(arr):
    stops = [
        'Rejection',
        'Disappointment',
        'Backstabbing Central',
        'Shattered Dreams Parkway'
    ]
    if all(stop in arr for stop in stops):
        return 'Smell my cheese you mother!'
    return 'No, seriously, run. You will miss it.'