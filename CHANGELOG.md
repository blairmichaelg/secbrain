# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation reorganization with guides/ and archive/ directories
- LICENSE file (MIT) for proper open source compliance
- Project URLs in pyproject.toml for better package metadata
- Enhanced .gitignore with better organization and Python patterns
- README files for all documentation directories
- CHANGELOG.md following Keep a Changelog format
- Additional badges in README (Python version)
- Enhanced pyproject.toml metadata with maintainers, additional classifiers, and changelog URL
- Professional README footer with license, acknowledgments, and updated date

### Changed
- Moved workflow and optimization guides to docs/guides/
- Moved implementation-specific docs to docs/archive/
- Moved utility scripts (test_research.py, validate-automation.py) to scripts/
- Updated all documentation links in README to reflect new structure
- Improved README header formatting with badges and description
- Updated scripts/README.md with comprehensive documentation

### Removed
- Empty file `0.8` from repository root
- Temporary files with random IDs (IMPLEMENTATION_SUMMARY_hyp-5430acaa.md, VALIDATION_REPORT_hyp-5430acaa.md)
- Duplicate comparison file (PR_139_vs_140_COMPARISON.md)

### Fixed
- All documentation links now point to correct locations
- Consistent formatting across documentation files

## [0.1.0] - 2024-12-25

### Added
- Initial release of SecBrain
- Multi-agent security bounty system
- Research integration with Perplexity API
- Advisor models with Gemini
- Guarded execution with ACLs and rate limits
- DeFi security templates for Solidity
- Immunefi platform integration
- Advanced research agent with pattern discovery
- Success metrics tracking
- Comprehensive security analysis workflow
- Property-based testing with Hypothesis
- Fuzzing with Foundry and Echidna
- Mutation testing with Mutmut
- Invariant testing for smart contracts
- SBOM generation and compliance checking
- Custom Semgrep security rules
- AI-powered engineering agent
- Free tier model support for all APIs

### Documentation
- Architecture documentation
- Workflow documentation
- Operations guide
- Threat model
- Testing strategies guide
- Solidity security patterns
- DeFi exploit protection guide
- Immunefi integration guide
- Git quick start guide
- Contributing guide
- Troubleshooting guide

[Unreleased]: https://github.com/blairmichaelg/secbrain/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/blairmichaelg/secbrain/releases/tag/v0.1.0
