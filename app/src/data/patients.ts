import { Patient } from '../types';

// Fixed reference date for the demo so every "weeks ago" / "months ago"
// framing in the copy lines up with the medication start dates below.
export const DEMO_TODAY = '2026-06-25';

export function formatDate(iso: string): string {
  return new Date(iso + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function daysBetween(a: string, b: string): number {
  const ms = new Date(b + 'T00:00:00').getTime() - new Date(a + 'T00:00:00').getTime();
  return Math.round(ms / (1000 * 60 * 60 * 24));
}

const maria: Patient = {
  id: 'maria-r',
  name: 'Maria R.',
  age: 82,
  sex: 'Female',
  riskLevel: 'elevated',
  diagnoses: ['Mild cognitive impairment', 'Hypertension', 'Insomnia', 'Urinary urgency'],
  comorbidities: {
    ckdStage: 'CKD stage 3a',
    egfr: 52,
    dialysis: false,
    bmi: 22,
    heartFailure: false,
    diabetes: true,
  },
  medications: [
    { id: 'm1', name: 'Amlodipine', dose: '5 mg daily', startDate: '2021-04-12', className: 'Calcium channel blocker', acb: 0, source: 'medication-list' },
    { id: 'm2', name: 'Lisinopril', dose: '10 mg daily', startDate: '2021-04-12', className: 'ACE inhibitor', acb: 0, source: 'medication-list' },
    { id: 'm3', name: 'Donepezil', dose: '5 mg nightly', startDate: '2025-12-15', className: 'Cholinesterase inhibitor (for MCI)', acb: 0, source: 'medication-list' },
    { id: 'm4', name: 'Oxybutynin', dose: '5 mg twice daily', startDate: '2026-05-28', className: 'Anticholinergic (bladder antimuscarinic)', acb: 3, source: 'medication-list' },
    { id: 'm5', name: 'Zolpidem', dose: '5 mg nightly', startDate: '2024-01-10', className: 'Sedative-hypnotic', acb: 1, source: 'medication-list' },
    { id: 'm6', name: 'Atorvastatin', dose: '20 mg nightly', startDate: '2019-06-01', className: 'Statin', acb: 0, source: 'medication-list' },
    { id: 'm7', name: 'Aspirin', dose: '81 mg daily', startDate: '2019-06-01', className: 'Antiplatelet', acb: 0, source: 'medication-list' },
  ],
  labs: [
    { name: 'eGFR', value: '52', unit: 'mL/min/1.73m2', flag: 'low' },
    { name: 'A1c', value: '7.1', unit: '%', flag: 'high' },
    { name: 'BMI', value: '22', unit: 'kg/m2', flag: 'normal' },
    { name: 'Blood pressure', value: '138/82', unit: 'mmHg', flag: 'normal' },
  ],
  complaint: {
    text: 'Dizziness and intermittent confusion',
    onsetDate: '2026-06-04',
    onsetDescription: 'Onset approximately 3 weeks ago, gradually noticed by family.',
  },
  signal: {
    status: 'cascade-detected',
    headline: 'This new presentation may be medication-driven.',
    clinicalQuestion: 'Could oxybutynin be driving Maria’s new dizziness and confusion?',
    rankedCauses: [
      {
        drug: 'Oxybutynin 5 mg twice daily',
        confidence: 'high',
        rationale:
          'A strong anticholinergic (illustrative ACB 3) started 4 weeks ago. It directly opposes donepezil, a cholinesterase inhibitor prescribed for her mild cognitive impairment, so she is effectively being prescribed against herself.',
        startDate: '2026-05-28',
        temporalLink: 'Started May 28, 2026. Symptoms began June 4, 2026, about 1 week later.',
        source: 'medication-list',
      },
    ],
    burden: {
      conventional: 3,
      adjusted: 4.2,
      driverExplanation:
        'Adjusted upward because CKD stage 3a (eGFR 52) slows renal clearance of oxybutynin metabolites, and diabetes-related autonomic changes increase her sensitivity to anticholinergic load.',
    },
    glassBox: {
      evidence: [
        'Oxybutynin 5 mg BID started May 28, 2026, four weeks before today.',
        'Dizziness and intermittent confusion began June 4, 2026, about one week after oxybutynin initiation.',
        'Donepezil (started December 15, 2025) is a cholinesterase inhibitor for MCI; oxybutynin’s anticholinergic action works directly against it.',
        'eGFR 52 mL/min (CKD stage 3a) slows clearance of oxybutynin metabolites, prolonging systemic anticholinergic exposure.',
      ],
      temporalReasoning:
        'Symptom onset trails oxybutynin initiation by about one week, a pattern consistent with cumulative anticholinergic load reaching a clinical threshold rather than a sudden reaction. Her other medications have been stable for six months or longer and do not share this timing.',
      literature:
        'Consistent with Beers Criteria guidance on anticholinergic burden in older adults. Illustrative reference for this demo, not a live literature lookup.',
      uncertainty: 'moderate',
      uncertaintyNote:
        'Moderate confidence. Overlapping contributors, such as zolpidem or orthostatic effects from her antihypertensives, cannot be fully excluded without an orthostatic blood pressure check.',
      ruledOut: [
        {
          candidate: 'Zolpidem 5 mg nightly',
          reason:
            'Can cause confusion, but it was started 8 months before this symptom onset. Stable exposure for that long without prior symptoms makes it a lower incremental contributor than a medication started 4 weeks ago.',
        },
        {
          candidate: 'Amlodipine and lisinopril (antihypertensives)',
          reason:
            'Could contribute to dizziness through orthostatic hypotension. Not excluded outright. MosaicRx recommends an orthostatic blood pressure check rather than dismissing this pathway.',
        },
        {
          candidate: 'Progression of underlying cognitive decline',
          reason:
            'The tight, one-week correlation with a specific medication start is more consistent with a drug effect than the gradual course typically expected from disease progression.',
        },
      ],
    },
    suggestedActions: [
      {
        id: 'a1',
        kind: 'taper',
        label: 'Taper/discontinue oxybutynin and trial mirabegron',
        noteTemplate:
          'Plan: Taper and discontinue oxybutynin 5 mg BID given anticholinergic burden concerns compounded by CKD stage 3a. Trial mirabegron as a non-anticholinergic alternative for urinary urgency. Counsel patient/family on expected timeline for symptom improvement and signs to report.',
      },
      {
        id: 'a2',
        kind: 'order',
        label: 'Order orthostatic BP check',
        noteTemplate:
          'Plan: Order orthostatic blood pressure measurement to evaluate a contributing orthostatic component from antihypertensive therapy alongside the anticholinergic cascade concern.',
      },
      {
        id: 'a3',
        kind: 'document',
        label: 'Document rationale',
        noteTemplate:
          'Assessment: Reviewed MosaicRx medication-driven cascade signal. Oxybutynin identified as most likely contributor to new dizziness and confusion given temporal proximity and comorbidity-adjusted anticholinergic burden. Rationale documented in chart for care team continuity.',
      },
      {
        id: 'a4',
        kind: 'dismiss',
        label: 'Dismiss (with reason)',
        noteTemplate: 'Signal reviewed and dismissed by clinician.',
      },
    ],
  },
};

const robert: Patient = {
  id: 'robert-t',
  name: 'Robert T.',
  age: 78,
  sex: 'Male',
  riskLevel: 'quiet',
  diagnoses: ['Hypertension', 'Type 2 diabetes', 'Hyperlipidemia', 'Benign prostatic hyperplasia', 'GERD', 'Osteoarthritis'],
  comorbidities: {
    ckdStage: undefined,
    egfr: 78,
    dialysis: false,
    bmi: 29,
    heartFailure: false,
    diabetes: true,
  },
  medications: [
    { id: 'r1', name: 'Lisinopril', dose: '20 mg daily', startDate: '2020-02-01', className: 'ACE inhibitor', acb: 0, source: 'medication-list' },
    { id: 'r2', name: 'Atorvastatin', dose: '40 mg nightly', startDate: '2021-11-03', className: 'Statin', acb: 0, source: 'medication-list' },
    { id: 'r3', name: 'Metformin', dose: '1000 mg twice daily', startDate: '2019-05-14', className: 'Biguanide antihyperglycemic', acb: 0, source: 'medication-list' },
    { id: 'r4', name: 'Tamsulosin', dose: '0.4 mg nightly', startDate: '2023-08-22', className: 'Alpha blocker (BPH)', acb: 0, source: 'medication-list' },
    { id: 'r5', name: 'Omeprazole', dose: '20 mg daily', startDate: '2022-01-10', className: 'Proton pump inhibitor', acb: 0, source: 'medication-list' },
    { id: 'r6', name: 'Aspirin', dose: '81 mg daily', startDate: '2019-05-14', className: 'Antiplatelet', acb: 0, source: 'medication-list' },
    { id: 'r7', name: 'Vitamin D3', dose: '2000 IU daily', startDate: '2020-06-01', className: 'Supplement', acb: 0, source: 'medication-list' },
    { id: 'r8', name: 'Acetaminophen', dose: '500 mg as needed', startDate: '2020-06-01', className: 'Analgesic', acb: 0, source: 'medication-list' },
  ],
  labs: [
    { name: 'eGFR', value: '78', unit: 'mL/min/1.73m2', flag: 'normal' },
    { name: 'A1c', value: '7.4', unit: '%', flag: 'high' },
    { name: 'TSH', value: 'pending', unit: '', flag: 'normal' },
    { name: 'Hemoglobin', value: '13.1', unit: 'g/dL', flag: 'normal' },
  ],
  complaint: {
    text: 'Generalized fatigue',
    onsetDate: '2026-05-20',
    onsetDescription: 'Gradual fatigue over about 5 weeks, no clear trigger reported.',
  },
  signal: {
    status: 'no-cascade',
    headline: 'No medication-driven cascade identified for this presentation.',
    clinicalQuestion: 'MosaicRx did not find a likely prescribing cascade behind this fatigue. A standard workup is reasonable.',
    rankedCauses: [],
    burden: {
      conventional: 0,
      adjusted: 0,
      driverExplanation: 'No medication on Robert’s active list carries a meaningful anticholinergic burden at his current doses.',
    },
    glassBox: {
      evidence: [
        'All 8 active medications have been stable for 6 months or longer, with no new starts or dose changes near symptom onset.',
        'None of Robert’s medications carry a moderate or strong anticholinergic burden rating.',
        'Fatigue is a nonspecific symptom with common non-medication explanations (anemia, thyroid dysfunction, sleep quality, deconditioning) worth ruling out directly.',
      ],
      temporalReasoning:
        'None of Robert’s eight medications show a start date within the past six months, and none carry a strong anticholinergic or sedating burden profile. Fatigue without a proximate medication change does not fit the reverse-causal pattern MosaicRx looks for.',
      literature:
        'Consistent with standard geriatric fatigue workup guidance. Illustrative reference for this demo, not a live literature lookup.',
      uncertainty: 'moderate',
      uncertaintyNote:
        'This does not rule out a medication contribution entirely. It reflects the absence of a specific, high-confidence culprit worth surfacing above a routine workup.',
      ruledOut: [
        {
          candidate: 'Metformin',
          reason: 'Stable dose for 7 years with normal renal function. Fatigue from metformin is uncommon at this dose and duration.',
        },
        {
          candidate: 'Tamsulosin',
          reason: 'Can cause mild fatigue or lightheadedness, but was started nearly 3 years ago with no temporal link to this new symptom.',
        },
        {
          candidate: 'Atorvastatin',
          reason: 'Statin-associated fatigue is possible, but the dose has been stable for over 4 years without a prior pattern of symptoms.',
        },
      ],
    },
    suggestedActions: [
      {
        id: 'r-a1',
        kind: 'workup',
        label: 'Order standard fatigue workup (CBC, TSH, metabolic panel)',
        noteTemplate:
          'Plan: MosaicRx found no medication-driven cascade for this presentation. Proceeding with standard fatigue workup including CBC, TSH, and comprehensive metabolic panel.',
      },
      {
        id: 'r-a2',
        kind: 'document',
        label: 'Document rationale',
        noteTemplate:
          'Assessment: Reviewed MosaicRx output. No prescribing cascade identified for Robert’s fatigue. Medication list reviewed and ruled out as documented. Proceeding with standard clinical workup.',
      },
      {
        id: 'r-a3',
        kind: 'dismiss',
        label: 'Dismiss (with reason)',
        noteTemplate: 'Signal reviewed and dismissed by clinician.',
      },
    ],
  },
};

const eleanor: Patient = {
  id: 'eleanor-k',
  name: 'Eleanor K.',
  age: 85,
  sex: 'Female',
  riskLevel: 'elevated',
  diagnoses: ['Hypertension', 'Osteoporosis', 'Chronic insomnia', 'Mild anxiety'],
  comorbidities: {
    ckdStage: undefined,
    egfr: 68,
    dialysis: false,
    bmi: 24,
    heartFailure: false,
    diabetes: false,
  },
  medications: [
    { id: 'e1', name: 'Lisinopril', dose: '10 mg daily', startDate: '2020-09-01', className: 'ACE inhibitor', acb: 0, source: 'medication-list' },
    { id: 'e2', name: 'Alendronate', dose: '70 mg weekly', startDate: '2019-03-15', className: 'Bisphosphonate', acb: 0, source: 'medication-list' },
    { id: 'e3', name: 'Calcium + Vitamin D', dose: '600 mg / 800 IU daily', startDate: '2019-03-15', className: 'Supplement', acb: 0, source: 'medication-list' },
    { id: 'e4', name: 'Sertraline', dose: '25 mg daily', startDate: '2023-02-10', className: 'SSRI', acb: 1, source: 'medication-list' },
    { id: 'e5', name: 'Acetaminophen', dose: '500 mg as needed', startDate: '2019-03-15', className: 'Analgesic', acb: 0, source: 'medication-list' },
    {
      id: 'e6',
      name: 'Diphenhydramine (Benadryl)',
      dose: '25 mg nightly',
      startDate: '2026-05-21',
      className: 'OTC antihistamine (strong anticholinergic)',
      acb: 3,
      source: 'patient-reported-otc',
    },
  ],
  labs: [
    { name: 'eGFR', value: '68', unit: 'mL/min/1.73m2', flag: 'normal' },
    { name: 'Blood pressure', value: '128/76', unit: 'mmHg', flag: 'normal' },
    { name: 'BMI', value: '24', unit: 'kg/m2', flag: 'normal' },
  ],
  complaint: {
    text: 'New confusion and a recent fall',
    onsetDate: '2026-06-08',
    onsetDescription: 'Family reports new confusion and a fall at home approximately 2 weeks ago.',
  },
  signal: {
    status: 'cascade-detected',
    headline: 'This new presentation may be medication-driven.',
    clinicalQuestion: 'Could an over-the-counter sleep aid be contributing to Eleanor’s new confusion and fall?',
    rankedCauses: [
      {
        drug: 'Diphenhydramine (Benadryl), 25 mg nightly, over-the-counter',
        confidence: 'high',
        rationale:
          'A strong anticholinergic (illustrative ACB 3) not on the formal medication list. Self-reported use for sleep, started about 5 weeks ago. Reconciled from the patient interview rather than the pharmacy fill record, so it does not appear in a standard medication reconciliation review.',
        startDate: '2026-05-21',
        temporalLink: 'Self-reported start May 21, 2026. Confusion and the fall were noted June 8, 2026, about 2.5 weeks later.',
        source: 'patient-reported-otc',
      },
    ],
    burden: {
      conventional: 0,
      adjusted: 3.4,
      driverExplanation:
        'The conventional score reflects only the formal medication list and misses the OTC diphenhydramine entirely. Once reconciled, the adjusted score rises sharply and is the highest-impact single agent in her profile.',
    },
    glassBox: {
      evidence: [
        'Diphenhydramine 25 mg nightly, self-reported for sleep, started May 21, 2026.',
        'This medication does not appear in the formal medication list or the pharmacy-fill record used to calculate the conventional burden score.',
        'New confusion and a fall were reported starting June 8, 2026, roughly two and a half weeks after she began taking it.',
        'Sertraline carries a mild anticholinergic rating but has been stable for over 3 years with no prior symptoms.',
      ],
      temporalReasoning:
        'The confusion and fall emerge in a window consistent with cumulative anticholinergic exposure from a strong agent taken nightly. No other medication on her active list changed in this timeframe.',
      literature:
        'Consistent with Beers Criteria guidance flagging first-generation antihistamines as high anticholinergic risk in older adults. Illustrative reference for this demo, not a live literature lookup.',
      uncertainty: 'moderate',
      uncertaintyNote:
        'Moderate confidence. Falls are multifactorial; a full fall risk assessment is warranted alongside addressing the anticholinergic exposure.',
      ruledOut: [
        {
          candidate: 'Sertraline',
          reason: 'Mild anticholinergic profile, but stable dose for over 3 years with no prior confusion reported.',
        },
        {
          candidate: 'Lisinopril-related orthostatic hypotension',
          reason:
            'A plausible contributor to the fall. Not excluded outright. MosaicRx recommends an orthostatic blood pressure check rather than dismissing this pathway.',
        },
        {
          candidate: 'New neurologic event (e.g. silent stroke)',
          reason:
            'Possible, but the tight temporal link to a known strong anticholinergic makes a medication effect the more likely first explanation to evaluate.',
        },
      ],
    },
    suggestedActions: [
      {
        id: 'e-a1',
        kind: 'taper',
        label: 'Discontinue OTC diphenhydramine, discuss non-anticholinergic sleep options',
        noteTemplate:
          'Plan: Counsel patient to discontinue over-the-counter diphenhydramine. Discuss non-anticholinergic options for insomnia, including sleep hygiene measures and, if needed, a non-anticholinergic agent.',
      },
      {
        id: 'e-a2',
        kind: 'order',
        label: 'Order orthostatic BP check and fall risk assessment',
        noteTemplate:
          'Plan: Order orthostatic blood pressure measurement and a formal fall risk assessment given the recent fall and possible anticholinergic and orthostatic contributors.',
      },
      {
        id: 'e-a3',
        kind: 'document',
        label: 'Document rationale',
        noteTemplate:
          'Assessment: Reviewed MosaicRx medication-driven cascade signal. Self-reported OTC diphenhydramine identified as most likely contributor to new confusion and fall. Rationale documented in chart for care team continuity.',
      },
      {
        id: 'e-a4',
        kind: 'dismiss',
        label: 'Dismiss (with reason)',
        noteTemplate: 'Signal reviewed and dismissed by clinician.',
      },
    ],
  },
};

export const PATIENTS: Patient[] = [maria, robert, eleanor];
