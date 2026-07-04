export type PointOfCareMode = 'previsit' | 'eprescribe' | 'chart-open';

export type Confidence = 'high' | 'moderate' | 'low';

export interface Medication {
  id: string;
  name: string;
  dose: string;
  startDate: string; // ISO date
  className: string;
  acb: 0 | 1 | 2 | 3; // illustrative anticholinergic cognitive burden scale
  source: 'medication-list' | 'patient-reported-otc';
}

export interface LabValue {
  name: string;
  value: string;
  unit: string;
  flag?: 'high' | 'low' | 'normal';
}

export interface Comorbidities {
  ckdStage?: string;
  egfr?: number;
  dialysis: boolean;
  bmi?: number;
  heartFailure: boolean;
  diabetes: boolean;
}

export interface PresentingComplaint {
  text: string;
  onsetDate: string;
  onsetDescription: string;
}

export interface RankedCause {
  drug: string;
  confidence: Confidence;
  rationale: string;
  startDate: string;
  temporalLink: string;
  source: 'medication-list' | 'patient-reported-otc';
}

export interface RuledOutCandidate {
  candidate: string;
  reason: string;
}

export interface BurdenScore {
  conventional: number;
  adjusted: number;
  driverExplanation: string;
}

export interface GlassBox {
  evidence: string[];
  temporalReasoning: string;
  literature: string;
  uncertainty: Confidence;
  uncertaintyNote: string;
  ruledOut: RuledOutCandidate[];
}

export type ActionKind = 'taper' | 'order' | 'workup' | 'document' | 'dismiss';

export interface SuggestedAction {
  id: string;
  label: string;
  kind: ActionKind;
  noteTemplate: string;
}

export interface MosaicSignal {
  status: 'cascade-detected' | 'no-cascade';
  headline: string;
  clinicalQuestion: string;
  rankedCauses: RankedCause[];
  burden: BurdenScore;
  glassBox: GlassBox;
  suggestedActions: SuggestedAction[];
}

export type RiskTier = 'low' | 'moderate' | 'high';

export interface FallRisk {
  tier: RiskTier;
  score: number; // illustrative composite, 0 to scaleMax
  scaleMax: number;
  bandLabel: string;
  factors: string[];
  instrumentNote: string;
}

export interface PredictedAdverseEvent {
  condition: string;
  likelihood: RiskTier;
  timeframe: string;
  rationale: string;
}

export interface PhenotypeRisk {
  fallRisk: FallRisk;
  // Empty array renders the "none of concern in this scope" state.
  predictedAdverseEvents: PredictedAdverseEvent[];
}

export interface Patient {
  id: string;
  name: string;
  age: number;
  sex: string;
  riskLevel: 'elevated' | 'moderate' | 'quiet';
  diagnoses: string[];
  comorbidities: Comorbidities;
  medications: Medication[];
  labs: LabValue[];
  complaint: PresentingComplaint;
  phenotypeRisk: PhenotypeRisk;
  signal: MosaicSignal;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  patientName: string;
  mode: PointOfCareMode;
  signalSurfaced: boolean;
  clinicianEngaged: boolean;
  action: string;
}
