// ========================================
// Mock Data — Multi-Agent Testing Platform
// ========================================

export const mockUser = {
  id: 'usr_01',
  name: 'Alex Morgan',
  email: 'alex.morgan@company.io',
  avatar: null,
  role: 'Admin',
  joinedAt: '2025-11-15T09:30:00Z',
};

export const mockProjects = [
  {
    id: 'proj_01',
    name: 'E-Commerce Checkout Flow',
    targetUrl: 'https://shop.example.com',
    status: 'completed',
    createdAt: '2026-07-28T10:00:00Z',
    lastRunAt: '2026-08-03T14:30:00Z',
    totalRuns: 12,
    passRate: 92,
    markdownSRS: '# E-Commerce Checkout\n\n## Overview\nTest the complete checkout flow including cart, payment, and order confirmation.\n\n## Test Scenarios\n1. Add items to cart\n2. Apply discount code\n3. Complete payment with Stripe\n4. Verify order confirmation email',
  },
  {
    id: 'proj_02',
    name: 'User Auth & Dashboard',
    targetUrl: 'https://app.example.com',
    status: 'running',
    createdAt: '2026-07-30T08:15:00Z',
    lastRunAt: '2026-08-04T09:00:00Z',
    totalRuns: 8,
    passRate: 87,
    markdownSRS: '# User Authentication\n\n## Overview\nTest login, registration, password reset, and dashboard access.\n\n## Test Scenarios\n1. Login with valid credentials\n2. Login with invalid credentials\n3. Register new account\n4. Password reset flow',
  },
  {
    id: 'proj_03',
    name: 'API Documentation Portal',
    targetUrl: 'https://docs.example.com',
    status: 'completed',
    createdAt: '2026-08-01T11:45:00Z',
    lastRunAt: '2026-08-02T16:20:00Z',
    totalRuns: 5,
    passRate: 100,
    markdownSRS: '# API Documentation\n\n## Overview\nValidate all API documentation pages render correctly.',
  },
  {
    id: 'proj_04',
    name: 'Landing Page Redesign',
    targetUrl: 'https://www.example.com',
    status: 'failed',
    createdAt: '2026-08-02T09:30:00Z',
    lastRunAt: '2026-08-03T11:15:00Z',
    totalRuns: 3,
    passRate: 45,
    markdownSRS: '# Landing Page\n\n## Overview\nTest the redesigned landing page for visual regressions and broken links.',
  },
  {
    id: 'proj_05',
    name: 'Admin Panel CRUD',
    targetUrl: 'https://admin.example.com',
    status: 'pending',
    createdAt: '2026-08-03T14:00:00Z',
    lastRunAt: null,
    totalRuns: 0,
    passRate: 0,
    markdownSRS: '# Admin Panel\n\n## Overview\nTest CRUD operations for all admin panel entities.',
  },
  {
    id: 'proj_06',
    name: 'Mobile Web App',
    targetUrl: 'https://m.example.com',
    status: 'completed',
    createdAt: '2026-07-25T16:00:00Z',
    lastRunAt: '2026-08-01T10:00:00Z',
    totalRuns: 15,
    passRate: 95,
    markdownSRS: '# Mobile Web App\n\n## Overview\nTest mobile-specific features and responsive behavior.',
  },
];

export const mockTestRuns = [
  {
    id: 'run_01',
    projectId: 'proj_01',
    projectName: 'E-Commerce Checkout Flow',
    status: 'completed',
    startTime: '2026-08-03T14:30:00Z',
    endTime: '2026-08-03T14:42:00Z',
    duration: 720,
    agent: 'TestMaster-v3',
    stepsCompleted: 9,
    totalSteps: 9,
  },
  {
    id: 'run_02',
    projectId: 'proj_02',
    projectName: 'User Auth & Dashboard',
    status: 'running',
    startTime: '2026-08-04T09:00:00Z',
    endTime: null,
    duration: null,
    agent: 'Navigator-AI',
    stepsCompleted: 5,
    totalSteps: 9,
  },
  {
    id: 'run_03',
    projectId: 'proj_04',
    projectName: 'Landing Page Redesign',
    status: 'failed',
    startTime: '2026-08-03T11:00:00Z',
    endTime: '2026-08-03T11:15:00Z',
    duration: 900,
    agent: 'VisionCheck-AI',
    stepsCompleted: 6,
    totalSteps: 9,
  },
  {
    id: 'run_04',
    projectId: 'proj_03',
    projectName: 'API Documentation Portal',
    status: 'completed',
    startTime: '2026-08-02T16:00:00Z',
    endTime: '2026-08-02T16:20:00Z',
    duration: 1200,
    agent: 'DocValidator-AI',
    stepsCompleted: 9,
    totalSteps: 9,
  },
  {
    id: 'run_05',
    projectId: 'proj_06',
    projectName: 'Mobile Web App',
    status: 'completed',
    startTime: '2026-08-01T09:30:00Z',
    endTime: '2026-08-01T10:00:00Z',
    duration: 1800,
    agent: 'MobileTest-AI',
    stepsCompleted: 9,
    totalSteps: 9,
  },
];

export const mockNotifications = [
  {
    id: 'notif_01',
    type: 'success',
    title: 'Test Run Completed',
    message: 'E-Commerce Checkout Flow passed all 9 steps.',
    time: '2 hours ago',
    read: false,
  },
  {
    id: 'notif_02',
    type: 'error',
    title: 'Test Run Failed',
    message: 'Landing Page Redesign failed at step 6.',
    time: '5 hours ago',
    read: false,
  },
  {
    id: 'notif_03',
    type: 'info',
    title: 'New Agent Available',
    message: 'VisionCheck-AI v2 is now available.',
    time: '1 day ago',
    read: true,
  },
  {
    id: 'notif_04',
    type: 'warning',
    title: 'API Rate Limit',
    message: 'You have used 85% of your monthly API calls.',
    time: '2 days ago',
    read: true,
  },
];

export const mockDashboardStats = {
  totalProjects: 6,
  activeRuns: 1,
  passRate: 86.5,
  avgDuration: '14m 32s',
  totalProjectsTrend: 12.5,
  activeRunsTrend: -25,
  passRateTrend: 3.2,
  avgDurationTrend: -8.1,
};

export const runSteps = [
  { id: 1, name: 'Initialize', description: 'Setting up test environment', icon: 'Zap' },
  { id: 2, name: 'Parse SRS', description: 'Analyzing requirements document', icon: 'FileText' },
  { id: 3, name: 'Plan Tests', description: 'AI generating test strategy', icon: 'GitBranch' },
  { id: 4, name: 'Setup Browser', description: 'Launching Playwright instance', icon: 'Globe' },
  { id: 5, name: 'Navigate', description: 'Opening target website', icon: 'ExternalLink' },
  { id: 6, name: 'Execute Tests', description: 'Running automated test cases', icon: 'Play' },
  { id: 7, name: 'Capture Results', description: 'Taking screenshots & recordings', icon: 'Camera' },
  { id: 8, name: 'Analyze', description: 'AI analyzing test outcomes', icon: 'Brain' },
  { id: 9, name: 'Generate Report', description: 'Creating detailed test report', icon: 'FileCheck' },
];

export const mockLogs = [
  { time: '14:30:01', level: 'info', message: '[AgentQA] Initializing test environment...' },
  { time: '14:30:02', level: 'info', message: '[AgentQA] Loading project configuration: E-Commerce Checkout Flow' },
  { time: '14:30:03', level: 'success', message: '[AgentQA] Environment ready ✓' },
  { time: '14:30:04', level: 'info', message: '[SRS Parser] Parsing markdown SRS document...' },
  { time: '14:30:05', level: 'info', message: '[SRS Parser] Found 4 test scenarios' },
  { time: '14:30:06', level: 'success', message: '[SRS Parser] SRS parsed successfully ✓' },
  { time: '14:30:07', level: 'info', message: '[AI Planner] Generating test strategy using GPT-4...' },
  { time: '14:30:10', level: 'info', message: '[AI Planner] Created 12 test cases across 4 scenarios' },
  { time: '14:30:11', level: 'success', message: '[AI Planner] Test plan ready ✓' },
  { time: '14:30:12', level: 'info', message: '[Playwright] Launching Chromium browser...' },
  { time: '14:30:14', level: 'info', message: '[Playwright] Browser version: Chromium 120.0.6099.109' },
  { time: '14:30:15', level: 'success', message: '[Playwright] Browser ready ✓' },
  { time: '14:30:16', level: 'info', message: '[Navigator] Opening https://shop.example.com...' },
  { time: '14:30:18', level: 'info', message: '[Navigator] Page loaded (2.1s)' },
  { time: '14:30:19', level: 'success', message: '[Navigator] Website accessible ✓' },
  { time: '14:30:20', level: 'info', message: '[Executor] Running test case 1/12: "Add single item to cart"' },
  { time: '14:30:25', level: 'success', message: '[Executor] Test 1/12 passed ✓' },
  { time: '14:30:26', level: 'info', message: '[Executor] Running test case 2/12: "Add multiple items"' },
  { time: '14:30:32', level: 'success', message: '[Executor] Test 2/12 passed ✓' },
  { time: '14:30:33', level: 'info', message: '[Executor] Running test case 3/12: "Remove item from cart"' },
  { time: '14:30:38', level: 'success', message: '[Executor] Test 3/12 passed ✓' },
  { time: '14:30:39', level: 'info', message: '[Executor] Running test case 4/12: "Apply discount SAVE20"' },
  { time: '14:30:44', level: 'warning', message: '[Executor] Discount applied but total calculation off by $0.01' },
  { time: '14:30:45', level: 'success', message: '[Executor] Test 4/12 passed (with warning) ✓' },
  { time: '14:30:46', level: 'info', message: '[Executor] Running test case 5/12: "Proceed to checkout"' },
  { time: '14:30:51', level: 'success', message: '[Executor] Test 5/12 passed ✓' },
  { time: '14:30:52', level: 'info', message: '[Executor] Running test case 6/12: "Fill shipping details"' },
  { time: '14:30:58', level: 'success', message: '[Executor] Test 6/12 passed ✓' },
  { time: '14:30:59', level: 'info', message: '[Executor] Running test case 7/12: "Payment with Stripe"' },
  { time: '14:31:05', level: 'success', message: '[Executor] Test 7/12 passed ✓' },
  { time: '14:31:06', level: 'info', message: '[Executor] Running test case 8/12: "Order confirmation"' },
  { time: '14:31:12', level: 'success', message: '[Executor] Test 8/12 passed ✓' },
  { time: '14:31:13', level: 'info', message: '[Executor] Running test case 9/12: "Invalid card number"' },
  { time: '14:31:18', level: 'success', message: '[Executor] Test 9/12 passed ✓' },
  { time: '14:31:19', level: 'info', message: '[Executor] Running test case 10/12: "Empty cart checkout"' },
  { time: '14:31:24', level: 'success', message: '[Executor] Test 10/12 passed ✓' },
  { time: '14:31:25', level: 'info', message: '[Executor] Running test case 11/12: "Session persistence"' },
  { time: '14:31:30', level: 'error', message: '[Executor] Test 11/12 FAILED — Cart not persisted after refresh' },
  { time: '14:31:31', level: 'info', message: '[Executor] Running test case 12/12: "Mobile viewport"' },
  { time: '14:31:36', level: 'success', message: '[Executor] Test 12/12 passed ✓' },
  { time: '14:31:37', level: 'info', message: '[Capture] Taking final screenshots...' },
  { time: '14:31:40', level: 'success', message: '[Capture] 24 screenshots captured ✓' },
  { time: '14:31:41', level: 'info', message: '[Analyzer] AI analyzing test results...' },
  { time: '14:31:50', level: 'info', message: '[Analyzer] Coverage: 92% | Passed: 11/12 | Failed: 1/12' },
  { time: '14:31:51', level: 'success', message: '[Analyzer] Analysis complete ✓' },
  { time: '14:31:52', level: 'info', message: '[Reporter] Generating markdown report...' },
  { time: '14:31:55', level: 'success', message: '[Reporter] Report generated successfully ✓' },
  { time: '14:31:56', level: 'success', message: '[AgentQA] ══════════════════════════════════════' },
  { time: '14:31:56', level: 'success', message: '[AgentQA] TEST RUN COMPLETE — 11/12 passed (92%)' },
  { time: '14:31:56', level: 'success', message: '[AgentQA] ══════════════════════════════════════' },
];

export const mockReport = `# Test Run Report — E-Commerce Checkout Flow

## Summary

| Metric | Value |
|--------|-------|
| **Status** | ✅ Passed |
| **Total Tests** | 12 |
| **Passed** | 11 |
| **Failed** | 1 |
| **Pass Rate** | 91.67% |
| **Duration** | 12m 00s |
| **Agent** | TestMaster-v3 |

## Test Results

### ✅ Passed Tests

1. **Add single item to cart** — Verified item appears in cart with correct quantity
2. **Add multiple items** — Cart correctly handles multiple different products
3. **Remove item from cart** — Item removed and cart total updated
4. **Apply discount SAVE20** — Discount applied successfully (⚠️ minor rounding issue)
5. **Proceed to checkout** — Checkout page loads with correct cart summary
6. **Fill shipping details** — Form validation works, address auto-complete functional
7. **Payment with Stripe** — Stripe Elements loads, test card accepted
8. **Order confirmation** — Confirmation page shows order number and summary
9. **Invalid card number** — Proper error message displayed for invalid cards
10. **Empty cart checkout** — Prevented with appropriate warning message
11. **Mobile viewport** — All elements responsive at 375px width

### ❌ Failed Tests

1. **Session persistence** — Cart contents not preserved after page refresh
   - **Expected**: Cart items persist across browser refresh
   - **Actual**: Cart is empty after refresh
   - **Likely Cause**: localStorage not being updated on cart change
   - **Severity**: High

## Recommendations

1. Fix session persistence bug — cart state should sync to localStorage
2. Investigate $0.01 rounding discrepancy in discount calculation
3. Consider adding more edge case tests for payment flow
4. Add accessibility tests for screen readers

## Screenshots

24 screenshots were captured during this test run and are available for download.
`;

export const mockErrorTrace = `Error: Cart persistence test failed
    at CartPersistence.verify (/tests/checkout/persistence.spec.ts:42:15)
    at async TestRunner.executeStep (/engine/runner.ts:128:9)
    at async TestExecutor.runCase (/engine/executor.ts:67:12)
    at async AgentOrchestrator.execute (/agents/orchestrator.ts:234:7)
    
Caused by: AssertionError: expected [] to deeply equal [{id: "prod_01", qty: 1}]
    at Object.deepEqual (/node_modules/chai/lib/chai/interface/assert.js:175:32)
    at CartPersistence.verifyCartState (/tests/checkout/persistence.spec.ts:38:14)
    
Browser Console Errors:
  [Warning] localStorage.setItem() was called but the quota has been exceeded
  [Error] Uncaught DOMException: Failed to execute 'setItem' on 'Storage'

Network Requests:
  POST /api/cart/sync — 500 Internal Server Error
  Response: {"error": "Cart sync service unavailable"}
`;

export const mockApiKeys = [
  { id: 'key_01', name: 'Production API Key', key: 'aq_live_k8x...9f2m', created: '2026-06-15', lastUsed: '2026-08-04', status: 'active' },
  { id: 'key_02', name: 'Development Key', key: 'aq_test_j3p...7h1n', created: '2026-07-01', lastUsed: '2026-08-03', status: 'active' },
  { id: 'key_03', name: 'CI/CD Pipeline', key: 'aq_ci_m2r...5k8w', created: '2026-07-20', lastUsed: '2026-08-01', status: 'active' },
];

export const databaseModels = {
  User: {
    name: 'User',
    collection: 'users',
    fields: [
      { name: '_id', type: 'ObjectId', required: true, description: 'Auto-generated MongoDB ID' },
      { name: 'username', type: 'String', required: true, description: 'Unique username (3-30 chars)', unique: true, index: true },
      { name: 'email', type: 'String', required: true, description: 'Unique email address', unique: true, index: true },
      { name: 'password', type: 'String', required: true, description: 'bcrypt hashed password' },
      { name: 'avatar', type: 'String', required: false, description: 'URL to avatar image' },
      { name: 'role', type: 'String', required: true, description: 'User role', default: 'user', enum: ['user', 'admin'] },
      { name: 'createdAt', type: 'Date', required: true, description: 'Account creation timestamp', default: 'Date.now' },
      { name: 'updatedAt', type: 'Date', required: true, description: 'Last update timestamp', default: 'Date.now' },
    ],
  },
  Project: {
    name: 'Project',
    collection: 'projects',
    fields: [
      { name: '_id', type: 'ObjectId', required: true, description: 'Auto-generated MongoDB ID' },
      { name: 'projectName', type: 'String', required: true, description: 'Human-readable project name' },
      { name: 'targetUrl', type: 'String', required: true, description: 'Website URL to test' },
      { name: 'markdownSRS', type: 'String', required: true, description: 'Markdown SRS document' },
      { name: 'ownerId', type: 'ObjectId', required: true, description: 'Reference to User._id', ref: 'User' },
      { name: 'status', type: 'String', required: true, description: 'Current project status', default: 'pending', enum: ['pending', 'running', 'completed', 'failed'] },
      { name: 'totalRuns', type: 'Number', required: true, description: 'Total test runs executed', default: 0 },
      { name: 'passRate', type: 'Number', required: false, description: 'Overall pass rate percentage' },
      { name: 'lastRunAt', type: 'Date', required: false, description: 'Timestamp of last test run' },
      { name: 'createdAt', type: 'Date', required: true, description: 'Project creation timestamp', default: 'Date.now' },
      { name: 'updatedAt', type: 'Date', required: true, description: 'Last update timestamp', default: 'Date.now' },
    ],
  },
  TestRun: {
    name: 'TestRun',
    collection: 'testruns',
    fields: [
      { name: '_id', type: 'ObjectId', required: true, description: 'Auto-generated MongoDB ID' },
      { name: 'projectId', type: 'ObjectId', required: true, description: 'Reference to Project._id', ref: 'Project' },
      { name: 'status', type: 'String', required: true, description: 'Run status', default: 'pending', enum: ['pending', 'running', 'completed', 'failed'] },
      { name: 'agent', type: 'String', required: true, description: 'AI agent used for this run' },
      { name: 'stepsCompleted', type: 'Number', required: true, description: 'Steps completed so far', default: 0 },
      { name: 'totalSteps', type: 'Number', required: true, description: 'Total steps in the pipeline', default: 9 },
      { name: 'logs', type: '[Object]', required: false, description: 'Array of log entries' },
      { name: 'errorTrace', type: 'String', required: false, description: 'Stack trace if failed' },
      { name: 'report', type: 'String', required: false, description: 'Markdown test report' },
      { name: 'screenshots', type: '[String]', required: false, description: 'Array of screenshot URLs' },
      { name: 'metrics', type: 'Object', required: false, description: 'CPU, memory, duration metrics' },
      { name: 'startTime', type: 'Date', required: true, description: 'Run start timestamp' },
      { name: 'endTime', type: 'Date', required: false, description: 'Run end timestamp' },
      { name: 'createdAt', type: 'Date', required: true, description: 'Record creation timestamp', default: 'Date.now' },
    ],
  },
};
