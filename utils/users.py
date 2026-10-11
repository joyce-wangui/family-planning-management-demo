"""DEMO-ONLY accounts for the public demonstration deployment."""

USERS = {'admin': {'name': 'Demo Administrator',
           'role': 'Administrator',
           'password_hash': '84b7e35a3eea0bf0ffb0b774ae8333a6:53e07075410a03c63e718f04e526cf76d0f8fb4b876b551050fb972a17dfb5f6'},
 'supervisor': {'name': 'Demo Supervisor',
                'role': 'Supervisor',
                'password_hash': 'edc9e1fde13db40eba528522b580f5ec:315731a9ddfb573709971486b6071142d735723c80018d1126a83a31927e3d84'},
 'provider': {'name': 'Demo FP Service Provider',
              'role': 'FP Service Provider',
              'password_hash': 'f7efdbe76cad1dd1b57e7352a5cefa7e:043d334140d6625ce13645fc62a5cd66007d7bf82b02785129770869b362f7d5'},
 'pharmacy': {'name': 'Demo Pharmacy Officer',
              'role': 'Pharmacy/Commodity Officer',
              'password_hash': 'add11dd9fa9672e018fac0275d591802:a05251dd38bf02c58e23278c6ebef2f752cca45f38263f74fc9476164626110b'}}
