# Research Validation - developer commands

python3 -m unittest discover -s tests -v
python3 scripts/build_site.py
python3 scripts/research_cli.py validate-skills
python3 scripts/research_cli.py seed-backlog --product eyewear --output build/research/eyewear-backlog.json
python3 scripts/research_cli.py plan --product eyewear --node "光学级聚碳酸酯" --output build/research/pc-plan.json
python3 scripts/research_cli.py audit-ledger --input research/examples/ledger.json
python3 scripts/research_cli.py audit-dossier --input research/examples/node-dossier.json

禁止将CLI的结构测试宣称为事实真伪审核；真伪审核需要原始材料与审阅者判断。
