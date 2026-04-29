def categorize(item):
    item = item.lower()

    if 'uber' in item or 'lyft' in item:
        return 'Transport'
    elif 'walmart' in item or 'kroger' in item:
        return 'Groceries'
    elif 'netflix' in item:
        return 'Entertainment'
    else:
        return 'Other'
