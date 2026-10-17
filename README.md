# Example Integration

<!-- badges:begin (generated from project metadata) -->
[![HACS](https://img.shields.io/static/v1?label=HACS&message=Add%20integration&color=41BDF5&style=flat&logo=homeassistantcommunitystore&logoColor=white)](https://my.home-assistant.io/redirect/hacs_repository/?owner=seb5594&repository=Home-Assistant-Integration-Template&category=integration) ![setup](https://img.shields.io/static/v1?label=setup&message=UI%20config%20flow&color=157F71&style=flat)<br>
![home assistant](https://img.shields.io/static/v1?label=home%20assistant&message=%E2%89%A5%202024.4.0&color=1877A5&style=flat) [![version](https://img.shields.io/static/v1?label=version&message=0.1.0&color=1877A5&style=flat)](https://github.com/seb5594/Home-Assistant-Integration-Template/releases) [![released](https://img.shields.io/github/release-date-pre/seb5594/Home-Assistant-Integration-Template?label=released&style=flat)](https://github.com/seb5594/Home-Assistant-Integration-Template/releases) [![checks](https://img.shields.io/github/actions/workflow/status/seb5594/Home-Assistant-Integration-Template/ci.yml?branch=main&label=checks&style=flat)](https://github.com/seb5594/Home-Assistant-Integration-Template/actions/workflows/ci.yml)<br>
[![downloads](https://img.shields.io/github/downloads/seb5594/Home-Assistant-Integration-Template/total?label=downloads&style=flat)](https://github.com/seb5594/Home-Assistant-Integration-Template/releases) [![latest release](https://img.shields.io/github/downloads/seb5594/Home-Assistant-Integration-Template/latest/total?label=latest%20release&style=flat)](https://github.com/seb5594/Home-Assistant-Integration-Template/releases/latest)<br>
[![stars](https://img.shields.io/github/stars/seb5594/Home-Assistant-Integration-Template?label=stars&style=flat)](https://github.com/seb5594/Home-Assistant-Integration-Template/stargazers) [![issues](https://img.shields.io/github/issues/seb5594/Home-Assistant-Integration-Template?label=issues&style=flat)](https://github.com/seb5594/Home-Assistant-Integration-Template/issues) [![updated](https://img.shields.io/github/last-commit/seb5594/Home-Assistant-Integration-Template?label=updated&style=flat)](https://github.com/seb5594/Home-Assistant-Integration-Template/commits/main)<br>
![tests](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fseb5594%2FHome-Assistant-Integration-Template%2Fbadges%2Ftests.json&style=flat) ![HACS zip](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fseb5594%2FHome-Assistant-Integration-Template%2Fbadges%2Fzip-size.json&style=flat) ![last build](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fseb5594%2FHome-Assistant-Integration-Template%2Fbadges%2Flast-build.json&style=flat)
<!-- badges:end -->

A starting point for a HACS integration with the shared pipeline already wired in: validation,
tests, HACS and manual ZIP packaging, GitHub releases and README badges.

## Using this template

1. Create a repository from this template, named `hass-<project>-integration`.
2. Rename `custom_components/example_integration/` and update the `domain` in `manifest.json`,
   `DOMAIN` in `const.py`, `filename` in `hacs.json` (`<domain>.zip`) and the repository URLs.
3. Replace the placeholder code and add real tests under `.github/tests/`. Add
   `requirements-dev.txt` to run them with pytest, or keep plain `unittest` files.
   `.github/ha_tests/` holds tests that run inside a real Home Assistant core; the Compatibility
   workflow runs them for every release from the `homeassistant` minimum in `hacs.json` upwards,
   so lower that minimum only as far as the tests pass.
4. Regenerate the badge block above and commit the result:

   ```bash
   git clone https://github.com/seb5594/hass-workflows .engine   # private; needs access
   python .engine/.scripts/readme.py
   ```

5. Raise `version` in `manifest.json` and add a `CHANGELOG.md` entry for every release. A new
   version on `main` publishes the HACS ZIP, the manual ZIP and checksums; `a`, `b` and `rc`
   suffixes (for example `1.0.0b1`) become pre-releases.

The two workflows, `.github/workflows/ci.yml` and `compat.yml`, call the shared engine at a pinned
commit and need the `ORCHESTRATION_PAT` secret. Project-specific rules can go into `.github/checks/*.py`.

<!-- support:begin (generated, shared text) -->
## Say thanks

All my projects are built in my spare time, just for the fun of it. Still, they take a lot of time and care, and many of the smart home gadgets I buy end up here because I want to make them cloud-free and smart-home ready. Every bit of support means a lot to me.

If my work helped you or turned out to be useful, show your appreciation with a hot drink for my next sleepless night.

[![Buy Me a Coffee](https://img.shields.io/static/v1?label=Support&message=Buy%20Me%20a%20Coffee&color=FFDD00&logo=buy-me-a-coffee&logoColor=black&style=for-the-badge)](https://buymeacoffee.com/seb5594) [![PayPal](https://img.shields.io/static/v1?label=Support&message=PayPal&color=0070BA&logo=paypal&logoColor=white&style=for-the-badge)](https://www.paypal.com/donate/?hosted_button_id=QMQPNRENXDN26)
<!-- support:end -->
