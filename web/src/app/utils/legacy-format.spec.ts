import { describe, expect, it } from 'vitest';
import { formatTaskLabel } from './legacy-format';

describe('formatTaskLabel', () => {
  it('formats priority and owner', () => {
    expect(formatTaskLabel({
      title: 'Task',
      description: 'Description',
      status: 'TODO',
      priority: 'high',
      owner: 'student'
    })).toBe('HIGH · STUDENT');
  });

  it('uses defaults for missing task details', () => {
    expect(formatTaskLabel({
      title: 'Task',
      description: 'Description',
      status: 'TODO'
    })).toBe('NORMAL · SIN-ASIGNAR');
  });

  it('returns a fallback label for missing task data', () => {
    expect(formatTaskLabel(null)).toBe('SIN-DATOS');
  });
});
