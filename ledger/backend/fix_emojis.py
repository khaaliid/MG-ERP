import re
import os

# Simple text replacements for Windows compatibility  
replacements = [
    ('🚀', '[STARTUP]'),
    ('📊', '[DATABASE]'), 
    ('✅', '[SUCCESS]'),
    ('❌', '[ERROR]'),
    ('🎉', '[SUCCESS]'),
    ('🏥', '[HEALTH]'),
    ('📋', '[LIST]'),
    ('🆕', '[CREATE]'),
    ('💵', '[TRANSACTION]'),
    ('📅', '[DATE]'),
    ('📝', '[DETAILS]'),
    ('🔢', '[REFERENCE]'),
    ('🔍', '[SEARCH]'),
    ('⚠️', '[WARNING]'),
    ('🔄', '[PROCESSING]'),
    ('💾', '[SAVE]'),
    ('🆔', '[ID]'),
    ('📄', '[DOCUMENT]'),
    ('🏦', '[ACCOUNT]'),
    ('🔐', '[SECURITY]'),
    ('🏛️', '[GOVERNANCE]'),
    ('👥', '[ROLES]'),
]

files_to_update = [
    'app/api/accounts.py',
    'app/api/transactions.py', 
    'app/services/ledger.py',
    'app/dependencies.py',
    'app/main.py',
    'app/api/router.py'
]

for file_path in files_to_update:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply replacements
        for emoji, text in replacements:
            content = content.replace(emoji, text)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'Updated {file_path}')