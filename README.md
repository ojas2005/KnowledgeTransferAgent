# Knowledge Transfer Agent

Create a developer onboarding guide for a **specific assigned task** from a repository. The agent scans likely files, extracts bounded line-numbered evidence, asks an OpenAI model for a structured guide, and rejects citations that do not point to the supplied evidence.

A guide covers the module overview, relevant files, execution flow, API dependencies, database relationships, conventions, local setup, and first steps for the task. Sections without evidence stay empty and are called out as unknowns.

