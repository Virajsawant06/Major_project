
from dotenv import load_dotenv
load_dotenv()
from src.intelligence.brain import AttackBrain
brain = AttackBrain()
report = brain.attack('http://testphp.vulnweb.com')
print('Findings:', report['total_findings'])
print('Tools used:', report['tool'])
