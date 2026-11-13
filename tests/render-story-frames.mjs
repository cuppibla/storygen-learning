// Credential-free SSR regression check. Run after npm ci in 04b's frontend.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const frontend = path.join(root, '04b_Manual_Deployment_Done/frontend');
const require = createRequire(path.join(frontend, 'package.json'));
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const temp = fs.mkdtempSync(path.join(frontend, '.render-test-'));
try {
  for (const name of ['story-contract.ts', 'story-frames.tsx']) {
    const source = fs.readFileSync(path.join(root, 'shared/frontend', name), 'utf8').replace('@/lib/story-contract', './story-contract.js');
    const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022, esModuleInterop: true } });
    fs.writeFileSync(path.join(temp, name.replace(/\.tsx?$/, '.js')), outputText);
  }
  const StoryFrames = require(path.join(temp, 'story-frames.js')).default;
  const story = Array.from({ length: 6 }, (_, i) => `[SCENE ${i + 1}: Beat title ${i + 1}]\nStory paragraph ${i + 1}.`).join('\n\n');
  const images = [null, null, null, { index: 3, format: 'png', error: 'Unavailable', placeholder: true }, null, { index: 5, format: 'png', base64: 'cG5n' }];
  const html = renderToStaticMarkup(React.createElement(StoryFrames, { story, images, isGeneratingImages: true }));
  assert.equal((html.match(/<article/g) || []).length, 6);
  for (let i = 1; i <= 6; i++) assert.ok(html.includes(`Beat title ${i}`));
  assert.ok(html.includes('First Attempt'));
  assert.ok(html.includes('Setback'));
  assert.ok(html.includes('Illustration unavailable'));
  assert.ok(html.includes('Illustration for scene 6'));
  const freeHtml = renderToStaticMarkup(React.createElement(StoryFrames, { story, sceneCount: 4 }));
  assert.equal((freeHtml.match(/<article/g) || []).length, 4);
  assert.ok(freeHtml.includes('Four scenes, one story'));
  assert.ok(freeHtml.includes('Climax'));
  assert.ok(freeHtml.includes('Resolution'));
  assert.ok(!freeHtml.includes('First Attempt'));
  const unsegmented = renderToStaticMarkup(React.createElement(StoryFrames, { story: 'A plain paragraph.' }));
  assert.ok(unsegmented.includes('no scene boundaries'));
  assert.ok(unsegmented.includes('A plain paragraph.'));
  console.log('StoryFrames SSR checks passed: six cards, beats, indexed images, error and unsegmented states.');
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}
