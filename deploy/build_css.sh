#!/usr/bin/env bash
# Rebuild the minified stylesheets after editing static/assets/css/{style,responsive,theme-dark}.css
# (the site links the *.min.css files). Requires Node.js.
set -euo pipefail
cd "$(dirname "$0")/../static/assets/css"
for f in style responsive theme-dark google-updates ai-agents home-future inner-dark; do
  npx --yes clean-css-cli -O1 -o "$f.min.css" "$f.css"
  echo "$f.min.css rebuilt"
done

# One render-blocking request instead of eleven: bundle the site-wide stylesheets in their original cascade order.
# (flaticon.min.css lives in ../fonts with relative font URLs, so it stays a separate link; google-updates and
# ai-agents stay per-page because they carry global rules.) layout.html links site.bundle.min.css.
npx --yes clean-css-cli -O1 -o site.bundle.min.css   poppins.css bootstrap.min.css owl.theme.default.min.css owl.carousel.min.css boxicons.subset.css   meanmenu.min.css style.min.css responsive.min.css theme-dark.min.css home-future.min.css inner-dark.min.css
echo "site.bundle.min.css rebuilt"
  # google-updates.min.js: npx terser static/assets/js/google-updates.js -c -m -o static/assets/js/google-updates.min.js

  # ai-agents.min.js: npx terser static/assets/js/ai-agents.js -c -m -o static/assets/js/ai-agents.min.js

  # home-future.min.js: npx terser static/assets/js/home-future.js -c -m -o static/assets/js/home-future.min.js
