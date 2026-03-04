import fs from 'node:fs';

const commitMessageFile = process.argv[2];

if (!commitMessageFile) {
	console.error('ERROR: Missing commit message file path argument.');
	process.exit(1);
}

const raw = fs.readFileSync(commitMessageFile, 'utf8');
const message = raw.trim();
const header = message.split('\n')[0]?.trim() ?? '';

if (!header) {
	console.error('ERROR: Commit message header is empty.');
	process.exit(1);
}

const bypassPatterns = [/^Merge\s/i, /^Revert\s"/i];
const canBypass = bypassPatterns.some((pattern) => pattern.test(header));

if (canBypass) {
	process.exit(0);
}

const commitHeaderPattern =
	/^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|security|deps)(\([a-z0-9][a-z0-9._\/-]*\))?(!)?:\s.+$/;

if (!commitHeaderPattern.test(header)) {
	console.error('ERROR: Invalid commit message format.');
	console.error('Expected: type(scope): subject');
	console.error('Allowed types: feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|security|deps');
	console.error('Examples:');
	console.error('  feat(auth): support oauth login with github');
	console.error('  fix(api): handle empty tenant-id in login response');
	console.error('  docs: add open-source contribution guide');
	process.exit(1);
}

if (header.length > 72) {
	console.error(`ERROR: Commit header too long (${header.length}/72).`);
	console.error('Keep the subject concise and move details to the body.');
	process.exit(1);
}

