# User Instructions & Preferences Log

This file tracks all specific architectural decisions, feature requests, and workflow preferences explicitly requested by the user during the development of VoxSales.

## Architectural Decisions
1. **Multi-Tenant SaaS Focus:** The system must not just be a single agent for Mass Drips, but a fully scalable, sellable platform where other businesses can sign up, configure their own agents, and launch campaigns.
2. **Database Choice:** Switched from PostgreSQL to **MongoDB**. Using async Motor driver. Pydantic is used for strict schema validation before inserting into MongoDB.

## Feature Requests
1. **Auto-Scraper (Pro Feature):** Added ability for users to input a website URL so the system can automatically crawl, chunk, and index FAQs, policies, and products into their ChromaDB RAG.
2. **Auto Lead Generator (Pro Feature):** Added ability to scrape Google Maps/Directories (e.g., "Dentists in Bengaluru") to automatically find phone numbers and populate campaign lead queues.

## Workflow Preferences
1. **Response Format:** Every response during the coding phase MUST include the following 4 sections separately:
   - Checklist
   - Approach
   - Future Thoughts
   - What is Done
2. **Documentation Tracking:** Always create separate files and note down what the user has explicitly requested to keep a record of decisions (this file).
