GITHUB_DOMAINS = {
    "1": {"name": "AI & Machine Learning", "query": "topic:machine-learning"},
    "2": {"name": "Web Development", "query": "topic:web-development"},
    "3": {"name": "Backend & API", "query": "topic:backend"},
    "4": {"name": "Databases", "query": "topic:database"},
    "5": {"name": "DevOps & Cloud", "query": "topic:devops"},
    "6": {"name": "UI / UX Frameworks", "query": "topic:ui-framework"}
}

# Curated lists containing 15-20 Industry Giants per domain
# No API calls will be made to display this list.
CURATED_STANDARDS = {
    "1": {
        "category": "AI, ML & Data Science Giants",
        "items": [
            {"repo": "tensorflow/tensorflow", "desc": "An Open Source Machine Learning Framework for Everyone."},
            {"repo": "pytorch/pytorch", "desc": "Tensors and Dynamic neural networks in Python with strong GPU acceleration."},
            {"repo": "scikit-learn/scikit-learn", "desc": "Machine learning in Python."},
            {"repo": "dmlc/xgboost", "desc": "Scalable, Portable and Distributed Gradient Boosting."},
            {"repo": "microsoft/LightGBM", "desc": "A fast, distributed, high performance gradient boosting framework."},
            {"repo": "huggingface/transformers", "desc": "State-of-the-art Machine Learning for Pytorch, TensorFlow, and JAX."},
            {"repo": "langchain-ai/langchain", "desc": "Building applications with LLMs through composability."},
            {"repo": "run-llama/llama_index", "desc": "Data framework for your LLM applications."},
            {"repo": "ollama/ollama", "desc": "Get up and running with Llama 3, Mistral, Gemma, and other LLMs."},
            {"repo": "vllm-project/vllm", "desc": "A high-throughput and memory-efficient inference and serving engine for LLMs."},
            {"repo": "google-deepmind/alphafold", "desc": "Open source code for AlphaFold."},
            {"repo": "anthropic/anthropic-sdk-python", "desc": "The official Python library for the Anthropic API."},
            {"repo": "ggerganov/llama.cpp", "desc": "LLM inference in C/C++."},
            {"repo": "karpathy/nanoGPT", "desc": "The simplest, fastest repository for training/finetuning medium-sized GPTs."},
            {"repo": "CompVis/stable-diffusion", "desc": "A latent text-to-image diffusion model."}
        ]
    },
    "2": {
        "category": "Web Frontend Ecosystem",
        "items": [
            {"repo": "facebook/react", "desc": "A declarative, efficient, and flexible JavaScript library for building user interfaces."},
            {"repo": "vuejs/core", "desc": "The progressive JavaScript framework."},
            {"repo": "vercel/next.js", "desc": "The React Framework."},
            {"repo": "sveltejs/svelte", "desc": "Cybernetically enhanced web apps."},
            {"repo": "angular/angular", "desc": "The modern web developer's platform."},
            {"repo": "tailwindlabs/tailwindcss", "desc": "A utility-first CSS framework for rapid UI development."},
            {"repo": "twbs/bootstrap", "desc": "The most popular HTML, CSS, and JavaScript framework for developing responsive, mobile first projects on the web."},
            {"repo": "vitejs/vite", "desc": "Next generation frontend tooling. It's fast!"},
            {"repo": "d3/d3", "desc": "Bring data to life with SVG, Canvas and HTML."},
            {"repo": "mrdoob/three.js", "desc": "JavaScript 3D Library."}
        ]
    },
    "3": {
        "category": "Backend & API Frameworks",
        "items": [
            {"repo": "expressjs/express", "desc": "Fast, unopinionated, minimalist web framework for node."},
            {"repo": "django/django", "desc": "The Web framework for perfectionists with deadlines."},
            {"repo": "tiangolo/fastapi", "desc": "FastAPI framework, high performance, easy to learn, fast to code, ready for production."},
            {"repo": "pallets/flask", "desc": "The Python micro framework for building web applications."},
            {"repo": "spring-projects/spring-boot", "desc": "Spring Boot makes it easy to create stand-alone, production-grade Spring based Applications."},
            {"repo": "nestjs/nest", "desc": "A progressive Node.js framework for building efficient, scalable, and enterprise-grade server-side applications."},
            {"repo": "gin-gonic/gin", "desc": "Gin is a HTTP web framework written in Go (Golang)."},
            {"repo": "laravel/laravel", "desc": "A PHP framework for web artisans."},
            {"repo": "rails/rails", "desc": "Ruby on Rails."}
        ]
    },
    "4": {
        "category": "Mobile & Cross-Platform Development",
        "items": [
            {"repo": "flutter/flutter", "desc": "Flutter makes it easy and fast to build beautiful apps for mobile and beyond."},
            {"repo": "react-native-community/react-native", "desc": "A framework for building native applications using React."},
            {"repo": "ionic-team/ionic-framework", "desc": "A powerful cross-platform UI toolkit for building native-quality iOS, Android, and Progressive Web Apps."},
            {"repo": "tauri-apps/tauri", "desc": "Build smaller, faster, and more secure desktop applications with a web frontend."},
            {"repo": "electron/electron", "desc": "Build cross-platform desktop apps with JavaScript, HTML, and CSS."}
        ]
    },
    "5": {
        "category": "Databases & Storage Engines",
        "items": [
            {"repo": "redis/redis", "desc": "Redis is an in-memory database that persists on disk."},
            {"repo": "postgres/postgres", "desc": "Mirror of the official PostgreSQL GIT repository."},
            {"repo": "mongodb/mongo", "desc": "The MongoDB Database."},
            {"repo": "elastic/elasticsearch", "desc": "Free and Open, Distributed, RESTful Search Engine."},
            {"repo": "supabase/supabase", "desc": "The open source Firebase alternative."},
            {"repo": "prisma/prisma", "desc": "Next-generation ORM for Node.js & TypeScript | PostgreSQL, MySQL, MariaDB, SQL Server, SQLite, MongoDB and CockroachDB."},
            {"repo": "duckdb/duckdb", "desc": "DuckDB is an in-process SQL OLAP database management system."},
            {"repo": "ClickHouse/ClickHouse", "desc": "ClickHouse is a free analytics DBMS for big data."}
        ]
    },
    "6": {
        "category": "DevOps, Containers & Orchestration",
        "items": [
            {"repo": "docker/docker-ce", "desc": "Docker represents the open-source community development of Docker."},
            {"repo": "kubernetes/kubernetes", "desc": "Production-Grade Container Scheduling and Management."},
            {"repo": "hashicorp/terraform", "desc": "Terraform enables you to safely and predictably create, change, and improve infrastructure."},
            {"repo": "ansible/ansible", "desc": "Ansible is a radically simple IT automation platform."},
            {"repo": "prometheus/prometheus", "desc": "The Prometheus monitoring system and time series database."},
            {"repo": "grafana/grafana", "desc": "The open and composable observability and data visualization platform."}
        ]
    },
    "7": {
        "category": "Cybersecurity & Network Tools",
        "items": [
            {"repo": "sqlmapproject/sqlmap", "desc": "Automatic SQL injection and database takeover tool."},
            {"repo": "nmap/nmap", "desc": "Nmap - the Network Mapper. Github mirror of official SVN repository."},
            {"repo": "rapid7/metasploit-framework", "desc": "Metasploit Framework."},
            {"repo": "hashcat/hashcat", "desc": "World's fastest and most advanced password recovery utility."},
            {"repo": "wireshark/wireshark", "desc": "Read-only mirror of Wireshark's Git repository."},
            {"repo": "Sherlock-Project/sherlock", "desc": "Hunt down social media accounts by username across social networks."}
        ]
    },
    "8": {
        "category": "Developer Tooling & CLI Utilities",
        "items": [
            {"repo": "git/git", "desc": "Git Source Code Mirror."},
            {"repo": "junegunn/fzf", "desc": "A command-line fuzzy finder."},
            {"repo": "sharkdp/bat", "desc": "A cat(1) clone with wings."},
            {"repo": "tmux/tmux", "desc": "tmux source code."},
            {"repo": "neovim/neovim", "desc": "Vim-fork focused on extensibility and usability."},
            {"repo": "ohmyzsh/ohmyzsh", "desc": "A delightful community-driven (with 2,400+ contributors) framework for managing your zsh configuration."}
        ]
    }
}

TECH_SIGNALS = {
            "AI_ML": {
                "ai", "llm", "openai", "anthropic", "gemini", "claude", "deepmind", 
                "agentic", "neural network", "rag", "fine-tuning", "langchain", 
                "llama", "mistral", "machine learning", "computer vision", "nlp",
                "huggingface", "generative ai", "agi"
            },
            "DEVOPS_CLOUD": {
                "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "terraform", 
                "ci/cd", "devops", "cloud native", "serverless", "microservices", 
                "linux", "nginx", "infrastructure", "ansible", "jenkins", "argocd"
            },
            "DEV_ECOSYSTEM": {
                "python", "javascript", "typescript", "rust", "golang", "react", 
                "nextjs", "vue", "flutter", "framework", "open-source", "github", 
                "api", "sdk", "backend", "frontend", "release", "nodejs", "django"
            },
            "DATABASES_DATA": {
                "postgresql", "mongodb", "redis", "vector database", "pgvector", 
                "pinecone", "sql", "nosql", "database", "data pipeline", "snowflake",
                "databricks", "kafka", "elasticsearch"
            },
            "SECURITY": {
                "cybersecurity", "zero-day", "malware", "ransomware", "data breach", 
                "encryption", "auth", "vulnerability", "cve", "patch", "infosec",
                "pentesting", "phishing"
            },
            "GLOBAL_IT_TECH": {
                "google", "microsoft", "nvidia", "apple", "meta", "amazon", 
                "techcrunch", "y combinator", "startup", "acquisition", "ibm",
                "cisco", "oracle", "sap", "intel", "amd", "qualcomm", "tsmc"
            },
            "INDIAN_IT": {
                "tcs", "infosys", "wipro", "hcl", "tech mahindra", "l&t technology",
                "mphasis", "mindtree", "tata consultancy", "reliance jio", 
                "zomato", "swiggy", "flipkart", "paytm", "birlasoft"
            },
            "EMERGING_TECH": {
                "web3", "blockchain", "crypto", "iot", "ar/vr", "quantum computing",
                "robotics", "metaverse", "edge computing", "5g"
            }
        }

SOURCE_SCORES = {
            "techcrunch": 1.0, 
            "google news": 0.90, 
            "economic times": 0.85,
            "the verge": 0.90,
            "ars technica": 0.90,
            "wired": 0.85
        }