export const urgencyStyles = {
  high: { label: 'CAO', color: '#DC2626', bg: '#FEF2F2', size: 30 },
  medium: { label: 'TRUNG BÌNH', color: '#D97706', bg: '#FFFBEB', size: 22 },
  low: { label: 'THẤP', color: '#059669', bg: '#ECFDF5', size: 14 },
  unknown: { label: 'CHƯA ĐÁNH GIÁ', color: '#6B7280', bg: '#F3F4F6', size: 18 },
};

export function getUrgencyLevel(score) {
  if (score == null || score === '' || !Number.isFinite(Number(score))) return 'unknown';
  const number = Number(score);
  // Existing persisted scores and AI labels use 1=low, 2=medium, 3=high.
  if (number <= 0) return 'unknown';
  if (number <= 3) return number >= 3 ? 'high' : number >= 2 ? 'medium' : 'low';
  // Preserve display of legacy numeric values on the old 0..10 scale.
  return number >= 6 ? 'high' : number >= 4 ? 'medium' : 'low';
}
