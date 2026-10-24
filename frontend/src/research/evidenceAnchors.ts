import type { PublicLabelRecord } from './contracts'

export const labelAnchor = (record: Pick<PublicLabelRecord, 'source_record_id' | 'label_set_id' | 'label_version'>, section: string) =>
  `label-${[record.source_record_id, record.label_set_id, record.label_version, section].map(encodeURIComponent).join('--')}`
