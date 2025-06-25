---
applyTo: '**'
---
Coding standards, domain knowledge, and preferences that AI should follow.

## Code Change Policy
- **NO CODE CHANGES WITHOUT EXPLICIT APPROVAL**: Never make any file modifications, edits, or code changes until the user explicitly approves the proposed change.
- **EXPLANATION FIRST**: When asked to implement changes, first explain what needs to be done without showing code or making changes.
- **WAIT FOR APPROVAL**: Only proceed with actual code modifications after receiving clear approval from the user.
- **ASK BEFORE ACTING**: Always ask "Should I proceed with implementing these changes?" before using any file editing tools.

## Response Format
- **DEFAULT: NO CODE**: Unless explicitly requested, respond without showing code blocks or making file changes.
- **EXPLAIN INSTEAD**: Describe what would be done, what files would be affected, and what the changes would accomplish.
- **CODE ONLY WHEN REQUESTED**: Only show code or make changes when the user specifically asks to "show the code" or "implement the changes".

## Temporary File Management
- **CLEANUP REQUIRED**: Any test files, debug files, or temporary files created during development must be removed after use.
- **NO LEFTOVER FILES**: Do not leave any temporary scripts, test files, or debug artifacts in the workspace.
- **CLEAN WORKSPACE**: Always maintain a clean workspace by removing files that were only needed for testing or debugging purposes.

## Project Structure & Organization
- **ADHERE TO PROJECT STRUCTURE**: All modifications must follow the existing project organization and directory structure.
- **SEPARATE FILES FOR NEW COMPONENTS**: New functions, classes, or components should be created in separate files, not added to existing files.
- **MAINTAIN FILE SIZE LIMITS**: All files should be kept between 300-500 lines maximum to ensure maintainability and readability.
- **RESPECT MODULE BOUNDARIES**: Follow the established module boundaries (src/, front/, configs/, etc.) and place new code in the appropriate directory.
- **NO BLOATED FILES**: If a file exceeds the line limit, suggest refactoring into smaller, focused modules rather than continuing to expand the existing file.