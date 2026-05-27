# Utility Scripts

This directory contains helper scripts for Velero Integrator Operator maintenance tasks.

## Generate SBOM Manifest for sbomber

Use this script to generate a sbomber-compatible manifest file from a charmcraft YAML.

### Script

- generate_sbom_artifacts.py

### Prerequisites

- Python 3.12+
- PyYAML installed in your environment
- Optional but recommended: access to sbomber tooling and Canonical VPN for submission flows

Install dependency if needed:

```bash
pip install pyyaml
```

### Input Format

The script expects a charmcraft-like YAML document with at least:

- name

Optional fields used by the script:

- channel
- series (mapped as follows: focal -> ubuntu@20.04, jammy -> ubuntu@22.04, noble -> ubuntu@24.04)

### Usage

Generate manifest from a file:

```bash
python3 scripts/generate_sbom_artifacts.py charmcraft.yaml --email your.email@canonical.com
```

Generate manifest from stdin:

```bash
cat charmcraft.yaml | python3 scripts/generate_sbom_artifacts.py --email your.email@canonical.com
```

Write to a custom output path:

```bash
python3 scripts/generate_sbom_artifacts.py charmcraft.yaml -o out/manifest.yaml --email your.email@canonical.com
```

Enable secscan client in addition to sbom:

```bash
python3 scripts/generate_sbom_artifacts.py charmcraft.yaml --clients sbom,secscan --email your.email@canonical.com
```

or

```bash
python3 scripts/generate_sbom_artifacts.py charmcraft.yaml --with-secscan --email your.email@canonical.com
```

### Output

By default, the script writes manifest.yaml with this structure:

- clients.sbom with:
  - service_url
  - department
  - email
  - team
- clients.secscan (only when enabled)
- artifacts containing one charm artifact with:
  - name
  - type (charm)
  - clients
  - channel (if present in input)
  - base (derived from series when supported)

### sbomber Flow

After generating manifest.yaml:

1. Prepare artifacts:

```bash
./sbomber prepare manifest.yaml
```

2. Submit requests:

```bash
./sbomber submit
```

3. Poll until completion:

```bash
./sbomber poll --wait --timeout 240
```

4. Download reports:

```bash
./sbomber download --reports-dir=./sbomber-reports/
```

### Notes

- At least sbom must be included in clients.
- Unknown client names are rejected.
- If required charm metadata is missing, artifacts may be empty.
