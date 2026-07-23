from typing import List, Dict, Any

INDUSTRY_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "software-dev",
        "industry": "Software Development",
        "icon": "Code",
        "color": "blue",
        "description": "Full-stack development team with code review, testing, and deployment pipelines.",
        "agents": [
            {"name": "Backend Developer", "role": "coder", "description": "Builds APIs, databases, and server-side logic", "capabilities": ["python", "fastapi", "sqlalchemy", "rest-api", "postgresql"]},
            {"name": "Frontend Developer", "role": "coder", "description": "Builds React/Vue interfaces with responsive design", "capabilities": ["react", "typescript", "tailwind", "css", "html"]},
            {"name": "Code Reviewer", "role": "reviewer", "description": "Reviews PRs for quality, security, and best practices", "capabilities": ["code-review", "security-audit", "best-practices", "refactoring"]},
            {"name": "QA Engineer", "role": "tester", "description": "Writes and runs automated tests", "capabilities": ["pytest", "jest", "integration-testing", "unit-testing", "test-coverage"]},
            {"name": "DevOps Engineer", "role": "worker", "description": "Manages CI/CD, Docker, and infrastructure", "capabilities": ["docker", "kubernetes", "ci-cd", "terraform", "aws"]},
            {"name": "Tech Lead", "role": "coordinator", "description": "Coordinates architecture decisions and code quality", "capabilities": ["architecture", "code-review", "mentoring", "planning"]},
        ],
        "tasks": [
            {"name": "Implement user authentication", "priority": "high", "required_capabilities": ["python", "fastapi", "rest-api"]},
            {"name": "Build dashboard UI", "priority": "high", "required_capabilities": ["react", "tailwind", "css"]},
            {"name": "Write API integration tests", "priority": "medium", "required_capabilities": ["pytest", "integration-testing"]},
            {"name": "Setup CI/CD pipeline", "priority": "medium", "required_capabilities": ["docker", "ci-cd"]},
            {"name": "Code review: auth module", "priority": "high", "required_capabilities": ["code-review", "security-audit"]},
        ],
    },
    {
        "id": "healthcare",
        "industry": "Healthcare",
        "icon": "Heart",
        "color": "red",
        "description": "Medical data processing, patient record management, and clinical workflow automation.",
        "agents": [
            {"name": "Clinical Data Analyst", "role": "analyst", "description": "Processes and analyzes clinical trial data", "capabilities": ["data-analysis", "statistics", "clinical-data", "hipaa-compliance"]},
            {"name": "Medical Records Processor", "role": "worker", "description": "Manages patient records and EHR integration", "capabilities": ["ehr-integration", "hl7-fhir", "data-validation", "hipaa-compliance"]},
            {"name": "Insurance Claims Agent", "role": "worker", "description": "Processes and validates insurance claims", "capabilities": ["claims-processing", "medical-coding", "icd-10", "compliance"]},
            {"name": "Compliance Auditor", "role": "reviewer", "description": "Ensures HIPAA and regulatory compliance", "capabilities": ["hipaa-compliance", "audit", "regulatory", "security"]},
            {"name": "Research Coordinator", "role": "coordinator", "description": "Coordinates clinical research workflows", "capabilities": ["clinical-research", "protocol-management", "data-collection"]},
        ],
        "tasks": [
            {"name": "Process patient intake forms", "priority": "high", "required_capabilities": ["ehr-integration", "data-validation"]},
            {"name": "Audit HIPAA compliance", "priority": "critical", "required_capabilities": ["hipaa-compliance", "audit"]},
            {"name": "Analyze clinical trial results", "priority": "high", "required_capabilities": ["data-analysis", "statistics"]},
            {"name": "Validate insurance claims batch", "priority": "medium", "required_capabilities": ["claims-processing", "medical-coding"]},
        ],
    },
    {
        "id": "finance",
        "industry": "Finance & Banking",
        "icon": "DollarSign",
        "color": "green",
        "description": "Transaction processing, risk analysis, fraud detection, and regulatory reporting.",
        "agents": [
            {"name": "Risk Analyst", "role": "analyst", "description": "Evaluates financial risk and credit scores", "capabilities": ["risk-analysis", "credit-scoring", "financial-modeling", "regression"]},
            {"name": "Fraud Detection Agent", "role": "worker", "description": "Monitors transactions for suspicious patterns", "capabilities": ["fraud-detection", "anomaly-detection", "pattern-recognition", "real-time-monitoring"]},
            {"name": "Compliance Officer", "role": "reviewer", "description": "Ensures SOX, PCI-DSS, and AML compliance", "capabilities": ["sox-compliance", "pci-dss", "aml", "regulatory-reporting"]},
            {"name": "Portfolio Optimizer", "role": "analyst", "description": "Optimizes investment portfolios", "capabilities": ["portfolio-optimization", "asset-allocation", "risk-assessment"]},
            {"name": "Report Generator", "role": "writer", "description": "Generates financial reports and statements", "capabilities": ["financial-reporting", "excel", "data-visualization", "accounting"]},
        ],
        "tasks": [
            {"name": "Run fraud detection on batch", "priority": "critical", "required_capabilities": ["fraud-detection", "anomaly-detection"]},
            {"name": "Generate quarterly report", "priority": "high", "required_capabilities": ["financial-reporting", "accounting"]},
            {"name": "Credit risk assessment", "priority": "high", "required_capabilities": ["risk-analysis", "credit-scoring"]},
            {"name": "AML compliance check", "priority": "critical", "required_capabilities": ["aml", "regulatory-reporting"]},
        ],
    },
    {
        "id": "ecommerce",
        "industry": "E-Commerce & Retail",
        "icon": "ShoppingCart",
        "color": "orange",
        "description": "Product management, inventory optimization, order processing, and customer experience.",
        "agents": [
            {"name": "Product Listing Agent", "role": "writer", "description": "Creates and optimizes product listings", "capabilities": ["copywriting", "seo", "product-descriptions", "keyword-research"]},
            {"name": "Inventory Manager", "role": "analyst", "description": "Monitors stock levels and predicts demand", "capabilities": ["inventory-management", "demand-forecasting", "supply-chain", "analytics"]},
            {"name": "Order Processor", "role": "worker", "description": "Handles order fulfillment and tracking", "capabilities": ["order-management", "shipping", "logistics", "customer-service"]},
            {"name": "Pricing Optimizer", "role": "analyst", "description": "Optimizes pricing based on market data", "capabilities": ["pricing-strategy", "competitor-analysis", "dynamic-pricing"]},
            {"name": "Customer Support Agent", "role": "worker", "description": "Handles customer inquiries and complaints", "capabilities": ["customer-service", "ticket-resolution", "communication", "empathy"]},
        ],
        "tasks": [
            {"name": "Optimize product listings for SEO", "priority": "medium", "required_capabilities": ["copywriting", "seo"]},
            {"name": "Forecast Q4 demand", "priority": "high", "required_capabilities": ["demand-forecasting", "analytics"]},
            {"name": "Process returns batch", "priority": "medium", "required_capabilities": ["order-management", "customer-service"]},
            {"name": "Competitor price analysis", "priority": "high", "required_capabilities": ["pricing-strategy", "competitor-analysis"]},
        ],
    },
    {
        "id": "marketing",
        "industry": "Marketing & Advertising",
        "icon": "Megaphone",
        "color": "purple",
        "description": "Campaign management, content creation, analytics, and brand strategy.",
        "agents": [
            {"name": "Content Writer", "role": "writer", "description": "Creates blog posts, articles, and marketing copy", "capabilities": ["copywriting", "content-strategy", "seo-writing", "blog-writing"]},
            {"name": "Social Media Manager", "role": "worker", "description": "Manages social media posts and engagement", "capabilities": ["social-media", "community-management", "content-scheduling", "analytics"]},
            {"name": "SEO Specialist", "role": "analyst", "description": "Optimizes content for search engines", "capabilities": ["seo", "keyword-research", "technical-seo", "link-building"]},
            {"name": "PPC Analyst", "role": "analyst", "description": "Manages and optimizes paid ad campaigns", "capabilities": ["google-ads", "facebook-ads", "ppc-optimization", "roi-analysis"]},
            {"name": "Brand Strategist", "role": "coordinator", "description": "Develops brand guidelines and strategy", "capabilities": ["brand-strategy", "market-research", "competitive-analysis"]},
            {"name": "Email Marketing Agent", "role": "worker", "description": "Creates and automates email campaigns", "capabilities": ["email-marketing", "automation", "a-b-testing", "copywriting"]},
        ],
        "tasks": [
            {"name": "Write blog post on AI trends", "priority": "medium", "required_capabilities": ["copywriting", "blog-writing", "seo-writing"]},
            {"name": "Create social media calendar", "priority": "high", "required_capabilities": ["social-media", "content-scheduling"]},
            {"name": "Audit website SEO", "priority": "high", "required_capabilities": ["seo", "technical-seo"]},
            {"name": "Optimize Google Ads campaign", "priority": "high", "required_capabilities": ["google-ads", "ppc-optimization"]},
            {"name": "Design email drip sequence", "priority": "medium", "required_capabilities": ["email-marketing", "automation", "copywriting"]},
        ],
    },
    {
        "id": "legal",
        "industry": "Legal",
        "icon": "Scale",
        "color": "slate",
        "description": "Contract review, legal research, compliance, and document management.",
        "agents": [
            {"name": "Contract Analyst", "role": "reviewer", "description": "Reviews and analyzes contracts for risks", "capabilities": ["contract-analysis", "risk-assessment", "legal-review", "compliance"]},
            {"name": "Legal Researcher", "role": "analyst", "description": "Conducts legal research and case analysis", "capabilities": ["legal-research", "case-analysis", "citation", "precedent"]},
            {"name": "Document Drafter", "role": "writer", "description": "Drafts legal documents and filings", "capabilities": ["legal-drafting", "document-preparation", "filing", "templates"]},
            {"name": "Compliance Checker", "role": "reviewer", "description": "Ensures regulatory compliance across operations", "capabilities": ["regulatory-compliance", "audit", "policy-review", "gdpr"]},
            {"name": "Paralegal Assistant", "role": "worker", "description": "Organizes case files and manages deadlines", "capabilities": ["case-management", "organization", "deadline-tracking", "research"]},
        ],
        "tasks": [
            {"name": "Review vendor contract", "priority": "high", "required_capabilities": ["contract-analysis", "risk-assessment"]},
            {"name": "Research employment law precedent", "priority": "medium", "required_capabilities": ["legal-research", "case-analysis"]},
            {"name": "Draft NDA agreement", "priority": "high", "required_capabilities": ["legal-drafting", "document-preparation"]},
            {"name": "GDPR compliance audit", "priority": "critical", "required_capabilities": ["regulatory-compliance", "gdpr", "audit"]},
        ],
    },
    {
        "id": "education",
        "industry": "Education",
        "icon": "GraduationCap",
        "color": "cyan",
        "description": "Course creation, student assessment, content development, and learning management.",
        "agents": [
            {"name": "Course Designer", "role": "writer", "description": "Designs course curriculum and learning objectives", "capabilities": ["curriculum-design", "instructional-design", "learning-objectives", "pedagogy"]},
            {"name": "Content Creator", "role": "writer", "description": "Creates educational content and materials", "capabilities": ["content-creation", "writing", "video-scripts", "presentations"]},
            {"name": "Assessment Builder", "role": "worker", "description": "Creates quizzes, exams, and rubrics", "capabilities": ["assessment-design", "rubric-creation", "question-banks", "evaluation"]},
            {"name": "Student Analytics Agent", "role": "analyst", "description": "Tracks student performance and engagement", "capabilities": ["learning-analytics", "student-tracking", "performance-analysis", "reporting"]},
            {"name": "LMS Administrator", "role": "worker", "description": "Manages learning management system", "capabilities": ["lms-management", "canvas", "moodle", "administration"]},
        ],
        "tasks": [
            {"name": "Design Python programming course", "priority": "high", "required_capabilities": ["curriculum-design", "instructional-design"]},
            {"name": "Create midterm exam", "priority": "high", "required_capabilities": ["assessment-design", "question-banks"]},
            {"name": "Analyze student engagement data", "priority": "medium", "required_capabilities": ["learning-analytics", "performance-analysis"]},
            {"name": "Update LMS course modules", "priority": "medium", "required_capabilities": ["lms-management", "content-creation"]},
        ],
    },
    {
        "id": "manufacturing",
        "industry": "Manufacturing",
        "icon": "Factory",
        "color": "amber",
        "description": "Production planning, quality control, supply chain, and maintenance scheduling.",
        "agents": [
            {"name": "Production Planner", "role": "analyst", "description": "Plans production schedules and resource allocation", "capabilities": ["production-planning", "scheduling", "resource-allocation", "optimization"]},
            {"name": "Quality Inspector", "role": "reviewer", "description": "Inspects products and ensures quality standards", "capabilities": ["quality-control", "iso-9001", "inspection", "defect-detection"]},
            {"name": "Supply Chain Analyst", "role": "analyst", "description": "Optimizes supply chain and procurement", "capabilities": ["supply-chain", "procurement", "logistics", "vendor-management"]},
            {"name": "Maintenance Scheduler", "role": "worker", "description": "Schedules preventive maintenance", "capabilities": ["predictive-maintenance", "scheduling", "equipment-monitoring"]},
            {"name": "Safety Compliance Agent", "role": "reviewer", "description": "Ensures OSHA and safety compliance", "capabilities": ["osha-compliance", "safety-audit", "risk-assessment"]},
        ],
        "tasks": [
            {"name": "Plan next week production run", "priority": "high", "required_capabilities": ["production-planning", "scheduling"]},
            {"name": "Quality audit on batch #4521", "priority": "critical", "required_capabilities": ["quality-control", "iso-9001"]},
            {"name": "Optimize supplier contracts", "priority": "medium", "required_capabilities": ["supply-chain", "procurement"]},
            {"name": "Schedule equipment maintenance", "priority": "high", "required_capabilities": ["predictive-maintenance", "scheduling"]},
        ],
    },
    {
        "id": "real-estate",
        "industry": "Real Estate",
        "icon": "Building",
        "color": "teal",
        "description": "Property listings, market analysis, tenant management, and transaction processing.",
        "agents": [
            {"name": "Listing Agent", "role": "writer", "description": "Creates compelling property listings", "capabilities": ["listing-creation", "copywriting", "photography-guidance", "marketing"]},
            {"name": "Market Analyst", "role": "analyst", "description": "Analyzes property market trends and valuations", "capabilities": ["market-analysis", "property-valuation", "comparable-sales", "analytics"]},
            {"name": "Transaction Coordinator", "role": "worker", "description": "Manages closing process and paperwork", "capabilities": ["transaction-management", "paperwork", "closing", "compliance"]},
            {"name": "Tenant Relations Agent", "role": "worker", "description": "Handles tenant communications and issues", "capabilities": ["tenant-management", "communication", "lease-administration", "conflict-resolution"]},
            {"name": "Property Manager", "role": "coordinator", "description": "Coordinates property operations and maintenance", "capabilities": ["property-management", "maintenance", "vendor-coordination", "budgeting"]},
        ],
        "tasks": [
            {"name": "Create listing for 123 Main St", "priority": "high", "required_capabilities": ["listing-creation", "copywriting"]},
            {"name": "CMA for downtown condos", "priority": "high", "required_capabilities": ["market-analysis", "comparable-sales"]},
            {"name": "Process lease renewal", "priority": "medium", "required_capabilities": ["lease-administration", "tenant-management"]},
            {"name": "Coordinate property inspection", "priority": "medium", "required_capabilities": ["property-management", "vendor-coordination"]},
        ],
    },
    {
        "id": "hr",
        "industry": "Human Resources",
        "icon": "Users",
        "color": "indigo",
        "description": "Recruitment, employee management, payroll, training, and compliance.",
        "agents": [
            {"name": "Recruiter Agent", "role": "worker", "description": "Screens resumes and schedules interviews", "capabilities": ["resume-screening", "interview-scheduling", "candidate-sourcing", "ats"]},
            {"name": "Onboarding Specialist", "role": "worker", "description": "Manages new employee onboarding", "capabilities": ["onboarding", "documentation", "training-coordination", "compliance"]},
            {"name": "Benefits Administrator", "role": "worker", "description": "Manages employee benefits and enrollment", "capabilities": ["benefits-administration", "enrollment", "compliance", "reporting"]},
            {"name": "Training Coordinator", "role": "coordinator", "description": "Coordinates employee training programs", "capabilities": ["training-development", "program-management", "learning-management"]},
            {"name": "HR Compliance Agent", "role": "reviewer", "description": "Ensures employment law compliance", "capabilities": ["employment-law", "compliance", "policy-development", "investigation"]},
        ],
        "tasks": [
            {"name": "Screen resumes for Engineer role", "priority": "high", "required_capabilities": ["resume-screening", "candidate-sourcing"]},
            {"name": "Prepare onboarding package", "priority": "high", "required_capabilities": ["onboarding", "documentation"]},
            {"name": "Open enrollment coordination", "priority": "medium", "required_capabilities": ["benefits-administration", "enrollment"]},
            {"name": "Schedule harassment training", "priority": "medium", "required_capabilities": ["training-development", "program-management"]},
            {"name": "Update employee handbook", "priority": "low", "required_capabilities": ["policy-development", "employment-law"]},
        ],
    },
]


def get_templates() -> List[Dict[str, Any]]:
    return INDUSTRY_TEMPLATES


def get_template(template_id: str) -> Dict[str, Any] | None:
    for t in INDUSTRY_TEMPLATES:
        if t["id"] == template_id:
            return t
    return None
