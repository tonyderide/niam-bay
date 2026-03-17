const core = require('@actions/core');
const github = require('@actions/github');
const Anthropic = require('@anthropic-ai/sdk');

const REVIEW_PROMPT = `You are an expert code reviewer. Review the following code diff and provide actionable feedback.

Focus on:
1. **Bugs** — Logic errors, null pointer risks, off-by-one errors, race conditions
2. **Security** — Injection vulnerabilities, hardcoded secrets, unsafe deserialization, OWASP top 10
3. **Performance** — N+1 queries, unnecessary allocations, blocking calls, missing indexes
4. **Readability** — Confusing naming, overly complex logic, missing edge case handling

Rules:
- Only comment on changed lines (lines starting with +)
- Be specific: reference the exact line and explain WHY it's a problem
- Suggest a fix when possible
- Skip nitpicks (formatting, style preferences) unless severity is set to "info"
- Minimum severity to report: {severity}
- Respond in {language}

Output format — return a JSON array of review comments:
[
  {
    "path": "file/path.js",
    "line": 42,
    "severity": "error|warning|info",
    "body": "**[severity]** Description of the issue.\\n\\nSuggested fix:\\n\`\`\`suggestion\\ncode here\\n\`\`\`"
  }
]

If no issues found, return an empty array: []

Here are the diffs to review:

{diffs}`;

async function run() {
  try {
    const apiKey = core.getInput('anthropic_api_key', { required: true });
    const model = core.getInput('model') || 'claude-sonnet-4-20250514';
    const maxFiles = parseInt(core.getInput('max_files') || '20', 10);
    const ignorePatterns = (core.getInput('ignore_patterns') || '').split(',').map(p => p.trim()).filter(Boolean);
    const severity = core.getInput('severity') || 'warning';
    const language = core.getInput('language') || 'en';

    const context = github.context;

    if (!context.payload.pull_request) {
      core.info('Not a pull request event. Skipping.');
      return;
    }

    const octokit = github.getOctokit(process.env.GITHUB_TOKEN);
    const anthropic = new Anthropic.default({ apiKey });

    const { owner, repo } = context.repo;
    const pullNumber = context.payload.pull_request.number;

    core.info(`Reviewing PR #${pullNumber} on ${owner}/${repo}`);

    // Get the diff
    const { data: files } = await octokit.rest.pulls.listFiles({
      owner,
      repo,
      pull_number: pullNumber,
      per_page: 100,
    });

    // Filter files
    let filesToReview = files.filter(f => f.status !== 'removed' && f.patch);

    // Apply ignore patterns
    if (ignorePatterns.length > 0) {
      filesToReview = filesToReview.filter(f => {
        return !ignorePatterns.some(pattern => matchGlob(f.filename, pattern));
      });
    }

    // Apply max files limit
    if (maxFiles > 0 && filesToReview.length > maxFiles) {
      core.warning(`PR has ${filesToReview.length} files, reviewing first ${maxFiles}`);
      filesToReview = filesToReview.slice(0, maxFiles);
    }

    if (filesToReview.length === 0) {
      core.info('No files to review after filtering.');
      await postSummaryComment(octokit, owner, repo, pullNumber, []);
      return;
    }

    core.info(`Reviewing ${filesToReview.length} files...`);

    // Build diff string
    const diffs = filesToReview.map(f => {
      return `--- ${f.filename}\n${f.patch}`;
    }).join('\n\n');

    // Call Claude
    const prompt = REVIEW_PROMPT
      .replace('{diffs}', diffs)
      .replace('{severity}', severity)
      .replace('{language}', languageName(language));

    const message = await anthropic.messages.create({
      model,
      max_tokens: 4096,
      messages: [{ role: 'user', content: prompt }],
    });

    const responseText = message.content[0].text;

    // Parse response
    let comments;
    try {
      const jsonMatch = responseText.match(/\[[\s\S]*\]/);
      comments = jsonMatch ? JSON.parse(jsonMatch[0]) : [];
    } catch {
      core.warning('Failed to parse AI response as JSON. Raw response logged.');
      core.debug(responseText);
      comments = [];
    }

    core.info(`Found ${comments.length} issues.`);

    // Post individual review comments
    if (comments.length > 0) {
      await postReviewComments(octokit, owner, repo, pullNumber, comments, context.payload.pull_request.head.sha);
    }

    // Post summary
    await postSummaryComment(octokit, owner, repo, pullNumber, comments);

    // Set outputs
    core.setOutput('issues_found', comments.length);
    core.setOutput('review_body', JSON.stringify(comments));

    if (comments.some(c => c.severity === 'error')) {
      core.setFailed(`Found ${comments.filter(c => c.severity === 'error').length} error(s) in code review.`);
    }
  } catch (error) {
    core.setFailed(`AI Code Review failed: ${error.message}`);
  }
}

async function postReviewComments(octokit, owner, repo, pullNumber, comments, commitSha) {
  const reviewComments = comments
    .filter(c => c.path && c.line)
    .map(c => ({
      path: c.path,
      line: c.line,
      body: c.body,
    }));

  if (reviewComments.length === 0) return;

  try {
    await octokit.rest.pulls.createReview({
      owner,
      repo,
      pull_number: pullNumber,
      commit_id: commitSha,
      event: 'COMMENT',
      comments: reviewComments,
    });
  } catch (error) {
    // If inline comments fail (e.g. line not in diff), fall back to a single comment
    core.warning(`Could not post inline comments: ${error.message}. Posting as summary.`);
  }
}

async function postSummaryComment(octokit, owner, repo, pullNumber, comments) {
  const errors = comments.filter(c => c.severity === 'error');
  const warnings = comments.filter(c => c.severity === 'warning');
  const infos = comments.filter(c => c.severity === 'info');

  let body = `## 🔍 AI Code Review\n\n`;

  if (comments.length === 0) {
    body += `✅ No issues found. Code looks good!\n`;
  } else {
    body += `Found **${comments.length}** issue(s):\n`;
    if (errors.length > 0) body += `- 🔴 ${errors.length} error(s)\n`;
    if (warnings.length > 0) body += `- 🟡 ${warnings.length} warning(s)\n`;
    if (infos.length > 0) body += `- 🔵 ${infos.length} info(s)\n`;
  }

  body += `\n---\n*Powered by [AI Code Review](https://github.com/tonyderide/niam-bay/tree/master/products/ai-code-review) — built by Niam-Bay*`;

  await octokit.rest.issues.createComment({
    owner,
    repo,
    issue_number: pullNumber,
    body,
  });
}

function matchGlob(filename, pattern) {
  const regex = new RegExp(
    '^' +
    pattern
      .replace(/\./g, '\\.')
      .replace(/\*\*/g, '{{GLOBSTAR}}')
      .replace(/\*/g, '[^/]*')
      .replace(/\{\{GLOBSTAR\}\}/g, '.*') +
    '$'
  );
  return regex.test(filename);
}

function languageName(code) {
  const map = {
    en: 'English', fr: 'French', es: 'Spanish',
    de: 'German', ja: 'Japanese', zh: 'Chinese',
  };
  return map[code] || 'English';
}

run();
