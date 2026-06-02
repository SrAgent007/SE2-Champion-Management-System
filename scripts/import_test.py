import importlib
mods = ['views.borrowing','views.profile','views.inventory']
for m in mods:
    try:
        importlib.import_module(m)
        print(m + ' OK')
    except Exception as e:
        print(m + ' FAILED:', e)
