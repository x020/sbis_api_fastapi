#!/usr/bin/env python3
"""
Script to generate Caddyfile from template using environment variables.
"""
import os
import re
from pathlib import Path
from string import Template


def load_env_file(env_path: str = ".env") -> dict:
    """Load environment variables from .env file."""
    env_vars = {}

    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    else:
        print(f"Warning: {env_path} not found, using system environment variables")

    # Merge with system environment variables
    for key, value in os.environ.items():
        env_vars[key] = value

    return env_vars


def generate_caddyfile():
    """Generate Caddyfile from template."""
    # Load environment variables
    env_vars = load_env_file()

    # Set defaults
    defaults = {
        'DOMAIN': 'sabby.ru',
        'CADDY_EMAIL': 'admin@sabby.ru',
    }

    # Apply defaults for missing variables
    for key, default_value in defaults.items():
        if key not in env_vars:
            env_vars[key] = default_value
            print(f"Using default value for {key}: {default_value}")

    # Check required variables
    required_vars = ['DOMAIN']
    for var in required_vars:
        if var not in env_vars:
            raise ValueError(f"Required environment variable {var} is not set")

    # Read template
    template_path = Path("Caddyfile.template")
    if not template_path.exists():
        raise FileNotFoundError("Caddyfile.template not found")

    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Replace variables in template
    try:
        caddyfile_content = Template(template_content).safe_substitute(env_vars)
    except KeyError as e:
        raise ValueError(f"Missing required variable in template: {e}")

    # Validate generated content
    if '{{' in caddyfile_content or '}}' in caddyfile_content:
        raise ValueError("Some template variables were not replaced")

    # Write Caddyfile
    with open("Caddyfile", 'w', encoding='utf-8') as f:
        f.write(caddyfile_content)

    print("✅ Caddyfile generated successfully")
    print(f"📍 Domain: {env_vars['DOMAIN']}")
    print(f"📧 Email: {env_vars['CADDY_EMAIL']}")


def validate_caddyfile():
    """Validate generated Caddyfile syntax."""
    print("🔍 Validating Caddyfile...")

    # Basic validation - check for common issues
    with open("Caddyfile", 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []

    # Check for unmatched braces
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        issues.append(f"Unmatched braces: {open_braces} open, {close_braces} close")

    # Check for empty blocks
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if line.strip().endswith('{') and i < len(lines):
            next_line = lines[i].strip()
            if next_line == '' or next_line.startswith('#'):
                continue
            if not any(keyword in next_line for keyword in ['reverse_proxy', 'tls', 'log', 'header', 'rate_limit', 'encode']):
                issues.append(f"Line {i+1}: Block opened but no valid directive found")

    if issues:
        print("❌ Validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("✅ Caddyfile validation passed")
    return True


def main():
    """Main function."""
    print("🚀 Generating Caddyfile from template...")
    print("=" * 50)

    try:
        generate_caddyfile()
        if validate_caddyfile():
            print("\n🎉 Caddyfile is ready!")
            print("You can now start the services with:")
            print("  docker-compose up -d")
        else:
            print("\n⚠️ Caddyfile has validation issues but was generated")
            print("Please review and fix the issues before starting services")

    except Exception as e:
        print(f"❌ Error generating Caddyfile: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())