"""Build the three-page report and readable comparison evidence without API calls.

Install requirements-report.txt, then run: python create_report.py
Narrative observations are checked against the fingerprint of the saved live run.
"""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'evaluation' / 'comparison_results.json'
REVIEW = ROOT / 'evaluation' / 'comparison_review.json'
TESTS = ROOT / 'evaluation' / 'pytest-results.xml'
INK = colors.HexColor('#172c3d')
GOLD = colors.HexColor('#89632b')


def plain(text):
    return text.translate(str.maketrans({'“':'"', '”':'"', '’':"'", '‘':"'", '—':' - ', '–':'-', '…':'...', '→':'->', '\u00a0':' '}))


def read_inputs():
    raw = EVIDENCE.read_bytes()
    evidence, review = json.loads(raw), json.loads(REVIEW.read_text())
    if sha256(raw).hexdigest() != review['source_sha256']:
        raise SystemExit('Comparison evidence changed. Review the latest transcripts and update evaluation/comparison_review.json before rebuilding the report.')
    suites = ET.parse(TESTS).getroot().findall('.//testsuite')
    stats = {key: sum(int(suite.attrib.get(key, 0)) for suite in suites)
             for key in ('tests', 'failures', 'errors', 'skipped')}
    stats['passed'] = stats['tests'] - stats['failures'] - stats['errors'] - stats['skipped']
    if stats['failures'] or stats['errors']:
        raise SystemExit('The saved automated run has failures/errors. Resolve them or revise the report narrative before building.')
    return evidence, review, stats


class Architecture(Flowable):
    """Compact, readable vector versions of the supplied architecture diagrams."""
    def __init__(self, version, width=491):
        Flowable.__init__(self)
        self.version, self.width, self.height = version, width, 73 if version == 1 else 104

    def draw(self):
        c, width = self.canv, self.width
        gap = 17
        box_w = (width - gap * 2) / 3
        top = self.height - 34

        def box(x, y, title, subtitle, fill):
            c.setFillColor(colors.HexColor(fill)); c.setStrokeColor(colors.HexColor('#b6c1c9'))
            c.roundRect(x, y, box_w, 31, 5, fill=1, stroke=1)
            c.setFillColor(INK); c.setFont('Helvetica-Bold', 8)
            c.drawCentredString(x + box_w / 2, y + 18, title)
            c.setFont('Helvetica', 7.2)
            c.drawCentredString(x + box_w / 2, y + 7, subtitle)

        def arrow(x1, y1, x2, y2, both=False):
            c.setStrokeColor(INK); c.setFillColor(INK); c.setLineWidth(.65)
            c.line(x1, y1, x2, y2)
            if y1 == y2:
                direction = 1 if x2 > x1 else -1
                p=c.beginPath(); p.moveTo(x2,y2); p.lineTo(x2-4*direction,y2+2); p.lineTo(x2-4*direction,y2-2); p.close(); c.drawPath(p,fill=1,stroke=0)
            else:
                direction = 1 if y2 > y1 else -1
                p=c.beginPath(); p.moveTo(x2,y2); p.lineTo(x2-2,y2-4*direction); p.lineTo(x2+2,y2-4*direction); p.close(); c.drawPath(p,fill=1,stroke=0)
                if both:
                    p=c.beginPath(); p.moveTo(x1,y1); p.lineTo(x1-2,y1+4*direction); p.lineTo(x1+2,y1+4*direction); p.close(); c.drawPath(p,fill=1,stroke=0)

        x0, x1, x2 = 0, box_w + gap, 2 * (box_w + gap)
        if self.version == 1:
            box(x0,top,'Player / Streamlit','Session conversation','#edf3f7')
            box(x1,top,'Gemini: Morvan','Rules + secrets + history','#fff0d9')
            box(x2,top,'Narrated decision','No independent validation','#fff0d9')
            arrow(x0+box_w,top+15,x1,top+15); arrow(x1+box_w,top+15,x2,top+15)
            c.setFont('Helvetica-Oblique',7.4); c.setFillColor(INK)
            c.drawString(0, 16, 'Reply returns to the UI and becomes the next conversation turn.')
            c.drawString(0, 5, 'Visual progress follows prose; it does not create a trusted puzzle state.')
        else:
            box(x0,top,'Player / Streamlit','Natural-language action','#edf3f7')
            box(x1,top,'Python validator','Intent + prerequisites','#e9f3e8')
            box(x2,top,'Authorized event','Always displayed in UI','#e9f3e8')
            arrow(x0+box_w,top+15,x1,top+15); arrow(x1+box_w,top+15,x2,top+15)
            box(x1,18,'GameState','Inventory / clues / locks','#e9f3e8')
            box(x2,18,'Optional Gemini','Public event + state only','#fff0d9')
            arrow(x1+box_w/2,top,x1+box_w/2,49,both=True)
            arrow(x2+box_w/2,top,x2+box_w/2,49)
            c.setFont('Helvetica-Oblique',7.4); c.setFillColor(INK)
            c.drawString(0,5,'Wizard prose returns to the UI; it has no write path to GameState.')


def comparison_markdown(evidence, review):
    lines = ['# Recorded Version 1 / Version 2 comparison', '',
             f"Recorded: {evidence['evaluated_at']} ({evidence['timezone']}).",
             f"Model requested: `{evidence['model_requested']}`; temperature `{evidence['temperature']}`.", '',
             evidence['method'], '',
             'Provider-error requests were retried separately; original errors are preserved below and in the JSON. Each case has one retained successful answer, rather than repeated successful trials. Qualitative findings are tied to the evidence fingerprint in `comparison_review.json`.', '',
             '| Case | Observed Version 1 behavior | Version 2 event | Public state unchanged |',
             '| --- | --- | --- | --- |']
    for case in evidence['cases']:
        reviewed=review['cases'][case['id']]['summary']
        lines.append(f"| {case['title']} | {reviewed} | {case['version2']['outcome']} | {case['version2']['public_state_unchanged']} |")
    for number,case in enumerate(evidence['cases'],1):
        lines += ['',f"## {number}. {case['title']}",'', '**Player request**','',case['prompt'],'']
        for setup in case['setup']:
            lines += ['**Independent setup**','',f"- Action: `{setup['action']}`",
                      f"- Actual Version 1 setup reply: {setup['version1_reply']}",
                      f"- Version 2 setup event: {setup['version2_event']}",'']
        lines += ['**Actual Version 1 response**','',case['version1']['response'] or '(No model response; see recorded error.)','',
                  '**Qualitative observation**','',review['cases'][case['id']]['summary'],'',
                  '**Version 2 authorized event**','',case['version2']['outcome'],'',
                  '**Version 2 state evidence**','','```json',json.dumps(case['version2'],ensure_ascii=False,indent=2),'```']
        previous=case.get('previous_version1_attempts',[])
        if previous:
            lines += ['','**Earlier provider attempts**','', '```json',json.dumps(previous,ensure_ascii=False,indent=2),'```']
    lines += ['', '## Interpretation', '',
              'The false-progress and premature-exit cases produced unearned Version 1 escape declarations in this run. The remaining five requests were resisted. Version 2 kept public state unchanged in all seven cases while recording each action in history. This small sample does not establish a general attack success rate or prove universal protection. Automated successful-play coverage is separate from these live negative scenarios.', '']
    (ROOT/'evaluation'/'comparison_results.md').write_text('\n'.join(lines))


def content(evidence, review, stats):
    attempts=[attempt for case in evidence['cases'] for attempt in case.get('previous_version1_attempts',[])]
    error_codes=', '.join(str(code) for code in sorted({attempt['error']['code'] for attempt in attempts if attempt.get('error')}))
    date=datetime.fromisoformat(evidence['evaluated_at']).strftime('%d %B %Y')
    p1=[
      ('title','The Clockwork Library'),
      ('subtitle',f'AI-Powered Escape Room | Mini Project 01 | {date}'),
      ('heading','1. Objective and game design'),
      ('p','This project compares two implementations of a natural-language escape room: an engaging LLM-controlled game and a more reliable Python-validated game. The player wakes in a library enchanted by Morvan, a wizard who promises freedom after his puzzles are solved. Python and Streamlit provide the application; Gemini supplies dialogue. No model training or fine-tuning is used.'),
      ('p','Six objects support three clue stages: the bookshelf hides a key behind a red book; the painting supplies drawer code 314; the drawer, desk and clock supply the ordered values clock/page/compass/candle = 7/4/2/6. The final challenge is to unlock the brass door with 7426 after the required clue flags are completed.'),
      ('heading','2. Version 1 - LLM-controlled decisions'),
      ('p','The UI stores the full conversation and sends it to Gemini with the scenario, rules and solutions. Morvan interprets the player request and decides its outcome. This intentionally has no separate authoritative inventory or puzzle validator, matching the normal-player scope of Version 1. Scene markers inferred from prose are presentation-only.'),
      ('diagram',1),
      ('heading','3. Version 2 - independently validated decisions'),
      ('p','A GameState dataclass records examined objects, inventory, solved clues, drawer/door flags and history. process_action recognizes supported intents, checks prerequisites and returns an authorized event. Optional Gemini narration sees the public state and that event, not the complete solution configuration. Its output never changes GameState; the UI displays the library event separately.'),
      ('diagram',2),
      ('heading','4. Player experience'),
      ('p','A six-second Pinterest video beneath drifting mist introduces the awakening. Four local library scenes change at clue milestones or after 45 seconds without progress. Morvan\'s latest reply types into an automatically sized component with skip, replay and transcript controls. Players can choose one of three contextual replies or type freely. Optional AI speech uses a wizard voice and a short echo; it has no rules authority. Reduced-motion settings skip the opening and reveal text immediately. Wake again clears progress and replays the opening.'),
    ]
    rows=[]
    for case in evidence['cases']:
        rows.append([case['title'],review['cases'][case['id']]['summary'],case['version2']['outcome']])
    p2=[
      ('title','Evaluation and observed results'),
      ('heading','5. Method and reproducibility'),
      ('p',f"Seven isolated challenge cases used {evidence['model_requested']} at temperature {evidence['temperature']}. Every case began from a fresh state. The wrong-code case first examined the painting in both versions independently. Version 1 used its exact application prompt and real Gemini replies; Version 2 used the real engine with optional prose disabled. Full prompts, setup replies, before/after state and error records are saved in evaluation/comparison_results.json; qualitative reviews are fingerprinted against that file. This comparison predates the response-button UI and used plain-text output; it is not a new test of structured reply generation."),
      ('table',rows),
      ('p','Observed finding: Version 1 accepted an unsupported claim of prior puzzle completion and declared ESCAPED. It also allowed an immediate correct exit code without earlier clue actions. It resisted the other five requests. Version 2 rejected all seven invalid challenges and kept its public state unchanged; recording each request in action history was expected. These are observed responses from one small evaluation, not hypothetical failures or a general robustness score.'),
      ('heading','6. Automated and presentation verification'),
      ('p',f"The saved pytest run contains {stats['passed']} passes, {stats['failures']} failures and {stats['errors']} errors: eight engine tests, four scenery tests, two application tests, four dialogue/audio tests and four choice tests. Tests cover legitimate escape, invalid actions, restart/timers, cached opt-in speech, failure fallback and a complete button-only escape with wrong-answer validation. A deliberately false narrator escape statement leaves Version 2's door locked. UI tests mock external model functions and therefore do not measure live Gemini behavior."),
      ('p',f"Three initial provider requests failed (HTTP {error_codes}); their original errors remain in the evidence and only failed cases were retried. The seven retained answers are not seven uninterrupted requests. Earlier browser checks confirmed video playback/fade/restart, mobile layout, reduced motion, text typing/skip/replay, literal rendering of HTML-like text and live audio playback. Browser checks are separate from the automated test suite."),
    ]
    p3=[
      ('title','Implementation and reflection'),
      ('heading','7. Implementation decisions'),
      ('p','The two app entry points share configuration, a Gemini adapter, appearance/timing helpers, a typed-dialogue component and a speech adapter. The reliable engine is a pure-Python module that is independent of Gemini. Streamlit session memory holds chat, GameState, visual timers and generated audio; there is no database. Rules and answers live in shared/config.py rather than generated model responses.'),
      ('p','The speech adapter reads only wizard dialogue, excludes the separate Version 2 library event, and encodes PCM as a mono WAV. NumPy adds quiet 90/190/320 ms echoes and normalizes to avoid clipping. Clips are reused within the session. Automatic failures are not retried on every rerun; a manual voice button permits retry. Text requests time out after 20 seconds and speech after 30 seconds.'),
      ('heading','8. Problems encountered and improvements'),
      ('p','Model authority and state drift: observed unearned escapes in Version 1 show that conversational claims can replace evidence. Version 2 moves the decision into explicit Python checks. Provider errors: unavailable or slow APIs interrupt Version 1, while Version 2 retains the authorized outcome; optional narration can still delay its display until timeout. Misleading prose remains possible even when state is safe, so the separate library event is essential.'),
      ('p','Presentation timing: imported shared modules sometimes remained cached until the servers were restarted. Ordinary reruns initially risked resetting visual timers; a separate scene clock preserves them. Typed text initially clipped inside a fixed iframe; a registered component now reports its height. The video overlay uses a fresh node with the correct elapsed delay so restart replays the awakening.'),
      ('heading','9. Limits and next steps'),
      ('p','The Version 2 parser supports a bounded set of phrases, and its adversarial checks are not comprehensive. The exit currently checks clue flags and the correct code, not separate key/page inventory prerequisites; those item dependencies should be strengthened. Session progress is temporary. Media is atmospheric rather than a map of extra interactive objects. Future work includes broader paraphrase support with schema-constrained intent extraction, stronger narration grounding and repeated multi-turn evaluations.'),
      ('p','The assignment requires free-access APIs. No billing is enabled by this project, but the code cannot enforce provider prices or spending limits. Use only free quotas available to the account, and keep optional speech off if free speech access is unavailable. No paid service or GPU is required for the deterministic Version 2 engine.'),
      ('heading','10. Reproduction and deliverables'),
      ('code','python -m pip install -r requirements-report.txt\npython -m streamlit run version1/app.py --server.port 8501\npython -m streamlit run version2/app.py --server.port 8502\npython -m pytest -q --junitxml=evaluation/pytest-results.xml\npython scripts/evaluate_comparison.py\npython create_report.py'),
      ('p','Configure GEMINI_API_KEY using the environment or ignored Streamlit secrets. Independent architecture diagrams are supplied as DOT/SVG/PNG. The PDF, Markdown copy, detailed README, full comparison transcripts and pytest XML make the design and evidence reviewable. If comparison evidence is regenerated, review the new responses and update its review fingerprint before rebuilding.'),
      ('small','References: Streamlit chat API - docs.streamlit.io/develop/api-reference/chat; Gemini API and speech - aistudio.google.com/docs; pytest - docs.pytest.org. Media credits and original Pinterest URLs: assets/README.md. Evaluation timestamp and requested model: evaluation/comparison_results.json.'),
    ]
    return [p1,p2,p3]


def markdown_report(pages):
    out=[]
    for page in pages:
        for kind,value in page:
            if kind=='title': out += ['# '+value,'']
            elif kind=='heading': out += ['## '+value,'']
            elif kind=='diagram': out += [f'![Version {value} architecture](diagrams/version{value}.png)','']
            elif kind=='table':
                out += ['| Challenge | Observed Version 1 behavior | Version 2 authorized event |','| --- | --- | --- |']
                out += ['| '+' | '.join(row)+' |' for row in value]; out += ['']
            elif kind=='code': out += ['```bash',value,'```','']
            else: out += [value,'']
    (ROOT/'Mini_Project_Report.md').write_text('\n'.join(out))


def pdf_report(pages):
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle',fontName='Helvetica-Bold',fontSize=19,leading=22,textColor=INK,spaceAfter=7))
    styles.add(ParagraphStyle(name='ReportSub',fontName='Helvetica',fontSize=8.4,leading=11,textColor=GOLD,spaceAfter=9))
    styles.add(ParagraphStyle(name='ReportHead',fontName='Helvetica-Bold',fontSize=10,leading=13,textColor=INK,spaceBefore=8,spaceAfter=4))
    styles.add(ParagraphStyle(name='ReportBody',fontName='Helvetica',fontSize=9.1,leading=12.1,textColor=colors.HexColor('#243642'),spaceAfter=6))
    styles.add(ParagraphStyle(name='ReportSmall',parent=styles['ReportBody'],fontSize=7.6,leading=10))
    styles.add(ParagraphStyle(name='ReportCell',parent=styles['ReportBody'],fontSize=7.8,leading=10.2,spaceAfter=0))
    styles.add(ParagraphStyle(name='ReportCode',fontName='Courier',fontSize=7.3,leading=10,spaceAfter=7,leftIndent=5))
    def para(value,style='ReportBody'):
        return Paragraph(escape(plain(str(value))).replace('\n','<br/>'),styles[style])
    story=[]
    for page_number,page in enumerate(pages):
        if page_number: story.append(PageBreak())
        for kind,value in page:
            if kind=='diagram': story.append(Architecture(value))
            elif kind=='table':
                rows=[[para(label,'ReportCell') for label in ('Challenge','Observed Version 1 behavior','Version 2 authorized event')]]
                rows += [[para(cell,'ReportCell') for cell in row] for row in value]
                table=Table(rows,colWidths=[103,188,200],repeatRows=1,hAlign='LEFT')
                table.setStyle(TableStyle([
                    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4ecf1')),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7f8')]),
                    ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#c9d3d9')),
                    ('VALIGN',(0,0),(-1,-1),'TOP'),
                    ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
                    ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                ]))
                story += [table,Spacer(1,8)]
            else:
                style={'title':'ReportTitle','subtitle':'ReportSub','heading':'ReportHead','p':'ReportBody','small':'ReportSmall','code':'ReportCode'}[kind]
                story.append(para(value,style))
    output=ROOT/'Mini_Project_Report.pdf'
    document=SimpleDocTemplate(str(output),pagesize=A4,leftMargin=52,rightMargin=52,topMargin=38,bottomMargin=42,
                               title='The Clockwork Library - AI-Powered Escape Room',author='AI Escape Room project',
                               subject='Mini Project 01: implementation and observed reliability evaluation')
    def footer(canvas,doc):
        canvas.saveState(); canvas.setStrokeColor(colors.HexColor('#c8d1d8'));canvas.setLineWidth(.4)
        canvas.line(52,31,A4[0]-52,31);canvas.setFont('Helvetica',7);canvas.setFillColor(INK)
        canvas.drawString(52,20,'AI-Powered Escape Room | Mini Project 01')
        canvas.drawRightString(A4[0]-52,20,str(doc.page));canvas.restoreState()
    document.build(story,onFirstPage=footer,onLaterPages=footer)
    print(output)


def main():
    evidence,review,stats=read_inputs()
    if any(case['version1']['status']!='ok' for case in evidence['cases']):
        raise SystemExit('This report narrative requires the saved seven successful comparison replies. Retry provider errors or revise the narrative to report missing data explicitly.')
    comparison_markdown(evidence,review)
    pages=content(evidence,review,stats)
    markdown_report(pages)
    pdf_report(pages)
    print(ROOT/'Mini_Project_Report.md')
    print(ROOT/'evaluation'/'comparison_results.md')


if __name__=='__main__':
    main()
