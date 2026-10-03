#!/bin/bash
echo "=== GitHub API: sra-tools releases (via WSL) ==="
curl -sL --max-time 30 -A "Mozilla/5.0 (X11; Linux x86_64)" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/ncbi/sra-tools/releases?per_page=5" \
  | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
except Exception as e:
    print('parse fail:', e); print(sys.stdin.read()[:500]); sys.exit(0)
if isinstance(d, dict) and d.get('message'):
    print('API msg:', d['message']); sys.exit(0)
for r in d:
    print('release:', r.get('tag_name'), '| name:', r.get('name'))
    for a in r.get('assets', []):
        print('   ', a['name'], round(a['size']/1e6,1), 'MB')
        print('     ', a['browser_download_url'])
"
echo "=== 若上面为空, 查 tags ==="
curl -sL --max-time 30 -A "Mozilla/5.0" "https://api.github.com/repos/ncbi/sra-tools/tags?per_page=5" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print('tag:',t['name']) for t in d] if isinstance(d,list) else print(d)"
