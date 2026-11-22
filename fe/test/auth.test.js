import assert from 'node:assert/strict';
import test from 'node:test';
import { canOperate } from '../src/utils/access.js';

test('only operator/admin roles can operate the prototype UI', () => {
  assert.equal(canOperate(null), false);
  assert.equal(canOperate({ role: 'viewer' }), false);
  assert.equal(canOperate({ role: 'operator' }), true);
  assert.equal(canOperate({ role: 'admin' }), true);
});
