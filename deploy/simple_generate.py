#!/usr/bin/env python3
"""
Simple Caddyfile generator
"""
import os

def main():
    # Load .env
    env_vars = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    else:
        print("❌ .env file not found")
        return 1

    print(f"📍 Domain: {env_vars.get('DOMAIN', 'NOT FOUND')}")
    print(f"📧 Email: {env_vars.get('CADDY_EMAIL', 'NOT FOUND')}")

    # Read template
    if not os.path.exists('Caddyfile.template'):
        print("❌ Caddyfile.template not found")
        return 1

    with open('Caddyfile.template', 'r', encoding='utf-8') as f:
        template = f.read()

    # Replace variables
    caddyfile = template.replace('{{DOMAIN}}', env_vars.get('DOMAIN', 'localhost'))
    caddyfile = caddyfile.replace('{{CADDY_EMAIL}}', env_vars.get('CADDY_EMAIL', 'admin@localhost'))

    # Check if replacement worked
    if '{{DOMAIN}}' in caddyfile or '{{CADDY_EMAIL}}' in caddyfile:
        print("❌ Some variables were not replaced")
        return 1

    # Write Caddyfile
    with open('Caddyfile', 'w', encoding='utf-8') as f:
        f.write(caddyfile)

    print("✅ Caddyfile generated successfully")
    return 0

if __name__ == "__main__":
    exit(main())