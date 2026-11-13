import test from 'node:test';
import assert from 'node:assert/strict';
import { SCENE_COUNT, SCENE_BEATS, parseSceneMarkers, placeImage, emptyImageSlots, isActiveStoryEvent } from '../shared/frontend/story-contract.ts';

const story = Array.from({ length: 6 }, (_, i) => `[SCENE ${i + 1}: Title ${i + 1}]\nScene text ${i + 1}.`).join('\n\n');

test('six beats and six empty slots', () => {
  assert.equal(SCENE_COUNT, 6);
  assert.deepEqual([...SCENE_BEATS], ['setup', 'inciting_incident', 'first_attempt', 'setback', 'climax', 'resolution']);
  assert.deepEqual(emptyImageSlots(), [null, null, null, null, null, null]);
});

test('parses explicit indices and descriptive titles', () => {
  const scenes = parseSceneMarkers(story);
  assert.equal(scenes.length, 6);
  assert.equal(scenes[3].index, 3);
  assert.equal(scenes[3].title, 'Title 4');
  assert.equal(scenes[3].text, 'Scene text 4.');
});

test('out-of-order and missing markers never shift text into another scene', () => {
  const scenes = parseSceneMarkers('[SCENE 5: Fifth]\nFive.\n\n[SCENE 2: Second]\nTwo.');
  assert.deepEqual(scenes.map(s => s.index), [4, 1]);
  assert.equal(scenes[0].text, 'Five.');
});

test('legacy markers work; unsegmented text is not guessed into six scenes', () => {
  assert.equal(parseSceneMarkers('[SCENE 1]\nHello.')[0].title, 'Scene 1');
  assert.deepEqual(parseSceneMarkers('One paragraph. Another sentence!'), []);
});

test('duplicate markers do not overwrite the first scene', () => {
  const scenes = parseSceneMarkers('[SCENE 1]\nFirst.\n[SCENE 1]\nDuplicate.');
  assert.equal(scenes.length, 1);
  assert.equal(scenes[0].text, 'First.');
});

test('images land by index, including error placeholders and duplicate deliveries', () => {
  let slots = emptyImageSlots();
  slots = placeImage(slots, { index: 5, format: 'png', base64: 'last' });
  slots = placeImage(slots, { index: 3, format: 'png', error: 'Unavailable', placeholder: true });
  slots = placeImage(slots, { index: 5, format: 'png', base64: 'updated' });
  assert.equal(slots.length, 6);
  assert.equal(slots[5].base64, 'updated');
  assert.equal(slots[3].placeholder, true);
  assert.equal(slots[0], null);
});

test('invalid indices and stale request IDs cannot corrupt the board', () => {
  const initial = emptyImageSlots();
  for (const index of [-1, 6, 1.5, NaN]) assert.deepEqual(placeImage(initial, { index, format: 'png' }), initial);
  assert.deepEqual(placeImage(initial, { index: 0, format: 'png' }, 'old', 'new'), initial);
});


test('only events tagged with the active request may update a story', () => {
  assert.equal(isActiveStoryEvent('new', 'new'), true);
  assert.equal(isActiveStoryEvent('old', 'new'), false);
  assert.equal(isActiveStoryEvent(undefined, 'new'), false);
  assert.equal(isActiveStoryEvent(null, null), false);
});


test('four scene images stay within four slots', () => {
  const slots = emptyImageSlots(4);
  assert.equal(slots.length, 4);
  assert.deepEqual(placeImage(slots, { index: 4, format: 'png' }, undefined, undefined, 4), slots);
  assert.equal(placeImage(slots, { index: 3, format: 'png' }, undefined, undefined, 4)[3].index, 3);
});
