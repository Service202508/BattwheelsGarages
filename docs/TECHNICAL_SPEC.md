# Battwheels OS - Technical Specification & Architecture Document

**Version:** 1.0  
**Date:** February 16, 2026  
**Status:** Production Blueprint  
**Author:** Systems Architecture Team

---

## Executive Summary

Battwheels OS is a self-improving EV service platform designed to capture undocumented EV failures from field technicians, convert them into structured repair intelligence, and synchronize this knowledge across a distributed network of garage locations. This document provides the comprehensive technical specification for building a production-grade system that transforms every field repair into compounding intelligence.

**Core Value Proposition:** Every repair makes the system smarter. A technician discovers a solution in one location; within minutes, technicians across the entire network have access to that proven fix.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Failure Intelligence Pipeline](#2-failure-intelligence-pipeline)
3. [Integration Layer](#3-integration-layer)
4. [Scalability Design](#4-scalability-design)
5. [AI/ML Models](#5-aiml-models)
6. [Data Synchronization](#6-data-synchronization)
7. [Security & Governance](#7-security--governance)
8. [Continuous Improvement Feedback Loops](#8-continuous-improvement-feedback-loops)
9. [Operational Considerations](#9-operational-considerations)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

## 1. System Architecture

### 1.1 High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BATTWHEELS OS PLATFORM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Web App   │  │ Mobile App  │  │ Technician  │  │  Admin      │        │
│  │  (React)    │  │  (React    │  │   Portal    │  │  Dashboard  │        │
│  │             │  │   Native)   │  │             │  │             │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│         └────────────────┴────────────────┴────────────────┘               │
│                                   │                                         │
│                          ┌────────▼────────┐                               │
│                          │   API Gateway   │                               │
│                          │   (Kong/Nginx)  │                               │
│                          └────────┬────────┘                               │
│                                   │                                         │
│    ┌──────────────────────────────┼──────────────────────────────┐         │
│    │                              │                              │         │
│    ▼                              ▼                              ▼         │
│ ┌──────────────┐  ┌──────────────────────┐  ┌──────────────────┐          │
│ │   Garage     │  │    Failure           │  │   Marketplace    │          │
│ │   Operations │  │    Intelligence      │  │   API Service    │          │
│ │   Service    │  │    Engine            │  │                  │          │
│ └──────┬───────┘  └──────────┬───────────┘  └────────┬─────────┘          │
│        │                     │                       │                     │
│        │         ┌───────────▼───────────┐           │                     │
│        │         │   Diagnostics AI      │           │                     │
│        │         │   Service             │           │                     │
│        │         └───────────┬───────────┘           │                     │
│        │                     │                       │                     │
│    ┌───▼─────────────────────▼───────────────────────▼───┐                 │
│    │              Message Queue (RabbitMQ/Redis)         │                 │
│    └───┬─────────────────────┬───────────────────────┬───┘                 │
│        │                     │                       │                     │
│    ┌───▼───┐           ┌─────▼─────┐           ┌─────▼─────┐               │
│    │MongoDB│           │ PostgreSQL│           │   Redis   │               │
│    │(Docs) │           │ (Relational)│         │  (Cache)  │               │
│    └───────┘           └───────────┘           └───────────┘               │
│                                                                             │
│    ┌─────────────────────────────────────────────────────────┐             │
│    │           Object Storage (S3/MinIO)                     │             │
│    │    (Documents, Images, ML Models, Failure Cards)        │             │
│    └─────────────────────────────────────────────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Microservices Topology

| Service | Responsibility | Technology | Database | Scaling Strategy |
|---------|---------------|------------|----------|------------------|
| **Gateway Service** | API routing, rate limiting, auth | Kong/Nginx | Redis | Horizontal |
| **Auth Service** | Authentication, JWT, OAuth | FastAPI | PostgreSQL | Horizontal |
| **Garage Operations** | Tickets, jobs, scheduling | FastAPI | MongoDB | Horizontal |
| **Employee Service** | HR, payroll, attendance | FastAPI | MongoDB | Horizontal |
| **Failure Intelligence** | Failure cards, matching | FastAPI | MongoDB + Vector DB | Horizontal |
| **Diagnostics AI** | Root cause analysis, ML | FastAPI + Python | PostgreSQL | GPU-enabled |
| **Notification Service** | Email, SMS, WhatsApp | FastAPI | Redis + MongoDB | Horizontal |
| **Marketplace Service** | Parts, vendors, pricing | FastAPI | PostgreSQL | Horizontal |
| **Invoice Service** | Billing, GST, PDF gen | FastAPI | PostgreSQL | Horizontal |
| **Sync Service** | Cross-location sync | FastAPI | Redis + MongoDB | Horizontal |
| **Analytics Service** | Reporting, dashboards | FastAPI | TimescaleDB | Vertical |

### 1.3 Design Rationale

**Why Microservices?**
- **Independent Scaling:** Diagnostics AI needs GPU resources; Garage Operations needs high throughput
- **Fault Isolation:** Failure in notification service shouldn't affect core repairs
- **Team Autonomy:** Different teams can own different services
- **Technology Flexibility:** ML services can use Python/TensorFlow while core services use FastAPI

**Why MongoDB for Documents?**
- Flexible schema for failure cards (evolving structure)
- Native support for geospatial queries (location-based matching)
- Horizontal scaling with sharding
- JSON-native for complex nested structures

**Why PostgreSQL for Transactions?**
- ACID compliance for financial data (invoices, payments)
- Strong relational queries for reporting
- Proven reliability at scale

**Trade-offs Considered:**
- Monolith vs. Microservices: Chose microservices for scale despite operational complexity
- SQL vs. NoSQL: Hybrid approach - NoSQL for flexibility, SQL for transactions
- Self-hosted vs. Managed: Recommend managed services (Atlas, RDS) for reduced ops burden

---

## 2. Failure Intelligence Pipeline

### 2.1 End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FAILURE INTELLIGENCE PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   CAPTURE   │───▶│   ANALYZE   │───▶│   CREATE    │───▶│    STORE    │  │
│  │   (Field)   │    │   (AI/ML)   │    │   (Card)    │    │   (Index)   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                 │                  │                  │          │
│         ▼                 ▼                  ▼                  ▼          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Technician │    │  Root Cause │    │  Failure    │    │  Vector DB  │  │
│  │  Input Form │    │  Analysis   │    │  Card Gen   │    │  + MongoDB  │  │
│  │  + Photos   │    │  Engine     │    │             │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                  │          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │          │
│  │   ACCESS    │◀───│    SYNC     │◀───│   MATCH     │◀─────────┘          │
│  │ (Technician)│    │  (Network)  │    │   (Query)   │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│         │                 │                  │                              │
│         ▼                 ▼                  ▼                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  Suggested  │    │  Real-time  │    │  Semantic   │                     │
│  │  Solutions  │    │  Push to    │    │  Search +   │                     │
│  │  Ranking    │    │  All Nodes  │    │  Filtering  │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Failure Card Data Structure

```json
{
  "failure_card_id": "fc_abc123def456",
  "version": 3,
  "status": "verified",
  
  "vehicle_context": {
    "make": "Ather",
    "model": "450X",
    "variant": "Gen 3",
    "year": 2024,
    "mileage_km": 15000,
    "battery_cycles": 450,
    "firmware_version": "v4.2.1"
  },
  
  "failure_signature": {
    "symptom_codes": ["SYM_BATT_001", "SYM_CHRG_003"],
    "symptom_text": "Battery not charging beyond 80%, intermittent",
    "error_codes_reported": ["E401", "E402"],
    "component_affected": "BMS",
    "subsystem": "battery_management",
    "failure_mode": "degradation",
    "severity": "medium",
    "occurrence_pattern": "intermittent",
    "environmental_factors": {
      "temperature_range": "35-45C",
      "humidity": "high",
      "usage_pattern": "daily_commute"
    }
  },
  
  "diagnostic_evidence": {
    "photos": ["s3://failures/fc_abc123/photo1.jpg"],
    "videos": [],
    "sensor_logs": ["s3://failures/fc_abc123/bms_log.csv"],
    "diagnostic_tool_output": {
      "tool": "Ather Diagnostic Pro",
      "readings": {
        "cell_voltage_variance": 0.15,
        "temperature_delta": 8,
        "soc_accuracy": 92
      }
    }
  },
  
  "root_cause_analysis": {
    "primary_cause": "BMS cell balancing circuit failure",
    "secondary_causes": ["thermal stress", "manufacturing_defect"],
    "confidence_score": 0.87,
    "ai_reasoning": "Pattern matches 847 similar cases with BMS issues...",
    "human_verified": true,
    "verified_by": "tech_senior_001",
    "verification_date": "2026-02-15T10:30:00Z"
  },
  
  "resolution": {
    "solution_type": "component_replacement",
    "solution_steps": [
      {
        "step": 1,
        "action": "Disconnect battery pack",
        "duration_minutes": 10,
        "tools_required": ["insulated_gloves", "torque_wrench"]
      },
      {
        "step": 2,
        "action": "Replace BMS module (Part: BMS-450X-V3)",
        "duration_minutes": 30,
        "tools_required": ["hex_key_set", "multimeter"]
      },
      {
        "step": 3,
        "action": "Calibrate new BMS",
        "duration_minutes": 45,
        "tools_required": ["diagnostic_tablet"]
      }
    ],
    "parts_required": [
      {
        "part_id": "BMS-450X-V3",
        "name": "BMS Module Ather 450X",
        "quantity": 1,
        "cost_inr": 8500,
        "availability": "in_stock"
      }
    ],
    "labor_hours": 1.5,
    "total_repair_cost_estimate": 12000,
    "success_rate": 0.94
  },
  
  "matching_metadata": {
    "embedding_vector": [0.123, -0.456, ...],  // 768-dimensional
    "keywords": ["battery", "charging", "BMS", "80%", "intermittent"],
    "symptom_hash": "sha256:abc123...",
    "vehicle_category": "two_wheeler_electric"
  },
  
  "usage_statistics": {
    "times_matched": 234,
    "times_used_as_solution": 189,
    "success_confirmations": 178,
    "failure_reports": 11,
    "effectiveness_score": 0.94,
    "last_used": "2026-02-16T08:45:00Z"
  },
  
  "provenance": {
    "origin_garage_id": "garage_delhi_001",
    "origin_ticket_id": "tkt_xyz789",
    "created_by": "tech_deepak_001",
    "created_at": "2026-01-15T14:30:00Z",
    "last_updated": "2026-02-15T10:30:00Z",
    "update_history": [
      {
        "version": 2,
        "updated_by": "tech_rahul_002",
        "changes": ["added diagnostic photo", "refined steps"],
        "timestamp": "2026-02-01T09:00:00Z"
      }
    ]
  },
  
  "network_sync": {
    "sync_status": "synced",
    "last_sync": "2026-02-16T00:00:00Z",
    "available_at_locations": ["all"],
    "restriction_level": "none"
  }
}
```

### 2.3 Indexing Strategy

**Primary Indexes (MongoDB):**
```javascript
// Fast lookup by ID
db.failure_cards.createIndex({ "failure_card_id": 1 }, { unique: true })

// Vehicle-specific queries
db.failure_cards.createIndex({ 
  "vehicle_context.make": 1, 
  "vehicle_context.model": 1,
  "vehicle_context.year": 1 
})

// Symptom-based matching
db.failure_cards.createIndex({ "failure_signature.symptom_codes": 1 })
db.failure_cards.createIndex({ "failure_signature.component_affected": 1 })

// Full-text search
db.failure_cards.createIndex({ 
  "failure_signature.symptom_text": "text",
  "resolution.solution_steps.action": "text"
})

// Geospatial (for location-aware recommendations)
db.failure_cards.createIndex({ "provenance.origin_location": "2dsphere" })

// Effectiveness ranking
db.failure_cards.createIndex({ 
  "usage_statistics.effectiveness_score": -1,
  "usage_statistics.times_used_as_solution": -1 
})
```

**Vector Index (for Semantic Search):**
```python
# Using Pinecone/Weaviate/Milvus for embedding similarity
index_config = {
    "name": "failure-cards-semantic",
    "dimension": 768,  # BERT/sentence-transformers output
    "metric": "cosine",
    "pods": 2,
    "replicas": 2
}

# Hybrid search: keyword + semantic
def search_failure_cards(query_text, vehicle_context, limit=10):
    # Generate embedding
    query_embedding = model.encode(query_text)
    
    # Combine filters
    filters = {
        "vehicle_context.make": vehicle_context.make,
        "status": {"$in": ["verified", "provisional"]}
    }
    
    # Hybrid score = 0.6 * semantic_score + 0.4 * keyword_score
    results = vector_db.query(
        vector=query_embedding,
        filter=filters,
        top_k=limit * 2
    )
    
    # Re-rank with keyword matching
    return rerank_with_keywords(results, query_text)[:limit]
```

### 2.4 AI-Assisted Matching Algorithm

```python
class FailureMatchingEngine:
    """
    Multi-stage matching with progressive refinement
    """
    
    def match(self, incoming_failure: FailureInput) -> List[FailureCard]:
        # Stage 1: Exact match on error codes (fastest)
        exact_matches = self.exact_code_match(incoming_failure.error_codes)
        if exact_matches and exact_matches[0].confidence > 0.95:
            return exact_matches
        
        # Stage 2: Vehicle + symptom category match
        category_matches = self.category_match(
            vehicle=incoming_failure.vehicle,
            symptom_codes=incoming_failure.symptom_codes
        )
        
        # Stage 3: Semantic similarity on description
        semantic_matches = self.semantic_match(
            text=incoming_failure.description,
            vehicle_filter=incoming_failure.vehicle
        )
        
        # Stage 4: Ensemble ranking
        combined = self.ensemble_rank(
            exact=exact_matches,
            category=category_matches,
            semantic=semantic_matches,
            weights=[0.4, 0.3, 0.3]
        )
        
        # Stage 5: Filter by effectiveness
        filtered = [m for m in combined if m.effectiveness_score > 0.7]
        
        return filtered[:5]  # Top 5 recommendations
    
    def ensemble_rank(self, exact, category, semantic, weights):
        """Weighted combination of multiple match strategies"""
        all_cards = {}
        
        for i, card in enumerate(exact):
            all_cards[card.id] = all_cards.get(card.id, 0) + weights[0] * (1 / (i + 1))
        
        for i, card in enumerate(category):
            all_cards[card.id] = all_cards.get(card.id, 0) + weights[1] * (1 / (i + 1))
        
        for i, card in enumerate(semantic):
            all_cards[card.id] = all_cards.get(card.id, 0) + weights[2] * (1 / (i + 1))
        
        sorted_cards = sorted(all_cards.items(), key=lambda x: x[1], reverse=True)
        return [self.get_card(card_id) for card_id, _ in sorted_cards]
```

---

## 3. Integration Layer

### 3.1 Service Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INTEGRATION LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    API Gateway (Kong)                                │   │
│  │  • Rate Limiting (1000 req/min per garage)                          │   │
│  │  • Authentication (JWT validation)                                   │   │
│  │  • Request/Response transformation                                   │   │
│  │  • Circuit breaker patterns                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐            │
│         │                          │                          │            │
│         ▼                          ▼                          ▼            │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │ GARAGE OPS      │    │ FAILURE         │    │ MARKETPLACE     │        │
│  │ ADAPTER         │    │ INTELLIGENCE    │    │ ADAPTER         │        │
│  │                 │    │ ADAPTER         │    │                 │        │
│  │ • Ticket CRUD   │    │ • Card creation │    │ • Parts lookup  │        │
│  │ • Job scheduling│    │ • Matching API  │    │ • Vendor API    │        │
│  │ • Technician    │    │ • Sync triggers │    │ • Pricing       │        │
│  │   assignment    │    │                 │    │                 │        │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│           │                      │                      │                  │
│           └──────────────────────┼──────────────────────┘                  │
│                                  │                                         │
│                    ┌─────────────▼─────────────┐                           │
│                    │    Event Bus (RabbitMQ)   │                           │
│                    │                           │                           │
│                    │ Topics:                   │                           │
│                    │ • ticket.created          │                           │
│                    │ • ticket.resolved         │                           │
│                    │ • failure_card.created    │                           │
│                    │ • failure_card.matched    │                           │
│                    │ • sync.required           │                           │
│                    │ • notification.send       │                           │
│                    └───────────────────────────┘                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Integration Patterns

**Pattern 1: Synchronous API Calls (Critical Path)**
```python
# For real-time operations that need immediate response
class GarageOperationsAdapter:
    
    @circuit_breaker(failure_threshold=5, recovery_timeout=30)
    async def create_ticket(self, ticket_data: TicketCreate) -> Ticket:
        # 1. Validate input
        validated = self.validate(ticket_data)
        
        # 2. Create ticket
        ticket = await self.ticket_service.create(validated)
        
        # 3. Trigger async failure matching (non-blocking)
        await self.event_bus.publish("ticket.created", ticket.dict())
        
        return ticket
    
    @retry(max_attempts=3, backoff=exponential(base=2))
    async def get_suggested_solutions(self, ticket_id: str) -> List[FailureCard]:
        ticket = await self.ticket_service.get(ticket_id)
        return await self.failure_intelligence.match(ticket.symptoms)
```

**Pattern 2: Asynchronous Events (Non-Critical Path)**
```python
# For operations that don't need immediate response
class FailureIntelligenceAdapter:
    
    async def on_ticket_resolved(self, event: TicketResolvedEvent):
        """
        When a ticket is resolved, potentially create or update failure card
        """
        # 1. Analyze resolution
        analysis = await self.analyze_resolution(event.ticket, event.resolution)
        
        # 2. Decide: create new card or update existing
        if analysis.is_novel_failure:
            card = await self.create_failure_card(event, analysis)
            await self.event_bus.publish("failure_card.created", card.dict())
        elif analysis.improves_existing:
            await self.update_failure_card(analysis.matching_card_id, event)
        
        # 3. Trigger network sync
        await self.event_bus.publish("sync.required", {
            "type": "failure_card",
            "action": "upsert",
            "data": card.dict()
        })
```

**Pattern 3: Saga Pattern (Multi-Service Transactions)**
```python
class InvoiceGenerationSaga:
    """
    Coordinate invoice generation across multiple services
    """
    
    async def execute(self, ticket_id: str):
        saga_id = str(uuid.uuid4())
        
        try:
            # Step 1: Lock ticket
            await self.garage_ops.lock_ticket(ticket_id, saga_id)
            
            # Step 2: Calculate costs from failure card
            costs = await self.failure_intelligence.get_repair_costs(ticket_id)
            
            # Step 3: Get parts pricing
            parts_pricing = await self.marketplace.get_current_prices(costs.parts)
            
            # Step 4: Generate invoice
            invoice = await self.invoice_service.generate(
                ticket_id=ticket_id,
                costs=costs,
                parts_pricing=parts_pricing
            )
            
            # Step 5: Update ticket status
            await self.garage_ops.update_status(ticket_id, "invoiced")
            
            # Step 6: Send notification
            await self.event_bus.publish("notification.send", {
                "type": "invoice_generated",
                "invoice_id": invoice.invoice_id,
                "customer_email": invoice.customer_email
            })
            
            return invoice
            
        except Exception as e:
            # Compensating transactions
            await self.rollback(saga_id)
            raise
```

### 3.3 Error Handling & Fallbacks

```python
class IntegrationErrorHandler:
    
    FALLBACK_STRATEGIES = {
        "failure_matching": {
            "primary": "ai_matching_service",
            "fallback_1": "keyword_search_local",
            "fallback_2": "cached_recent_matches",
            "degraded_mode": "manual_search_prompt"
        },
        "parts_pricing": {
            "primary": "marketplace_api",
            "fallback_1": "cached_prices_24h",
            "fallback_2": "static_price_list",
            "degraded_mode": "price_tbd_flag"
        }
    }
    
    async def with_fallback(self, operation: str, primary_fn, *args, **kwargs):
        strategies = self.FALLBACK_STRATEGIES[operation]
        
        try:
            return await primary_fn(*args, **kwargs)
        except ServiceUnavailableError:
            logger.warning(f"{operation}: Primary failed, trying fallback_1")
            return await self.execute_fallback(strategies["fallback_1"], *args, **kwargs)
        except TimeoutError:
            logger.warning(f"{operation}: Timeout, using cached data")
            return await self.execute_fallback(strategies["fallback_2"], *args, **kwargs)
        except Exception as e:
            logger.error(f"{operation}: All fallbacks failed, degraded mode")
            return self.degraded_response(strategies["degraded_mode"])
```

---

## 4. Scalability Design

### 4.1 Database Sharding Strategy

**MongoDB Sharding (Failure Cards & Tickets)**
```javascript
// Shard key selection rationale:
// - garage_id: Ensures locality of data per garage
// - created_at: Enables time-based partitioning
// - Compound key prevents hotspots

sh.shardCollection("battwheels.failure_cards", {
  "provenance.origin_garage_id": 1,
  "created_at": 1
})

sh.shardCollection("battwheels.tickets", {
  "garage_id": 1,
  "created_at": 1
})

// Zone-based sharding for geographic distribution
sh.addShardTag("shard-north", "region_north")
sh.addShardTag("shard-south", "region_south")
sh.addTagRange(
  "battwheels.tickets",
  { "garage_id": "garage_delhi_", "created_at": MinKey },
  { "garage_id": "garage_delhi_~", "created_at": MaxKey },
  "region_north"
)
```

**PostgreSQL Partitioning (Financial Data)**
```sql
-- Time-based partitioning for invoices
CREATE TABLE invoices (
    invoice_id VARCHAR(50) PRIMARY KEY,
    garage_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    total_amount DECIMAL(12,2),
    gst_amount DECIMAL(12,2),
    -- ... other columns
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE invoices_2026_01 PARTITION OF invoices
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE invoices_2026_02 PARTITION OF invoices
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- Automated partition creation via pg_partman
```

### 4.2 Caching Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CACHING LAYERS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 1: Browser/App Cache (Client)                                       │
│  ├── Static assets (JS, CSS, images) - CDN                                 │
│  ├── User preferences - LocalStorage                                       │
│  └── Recent searches - IndexedDB                                           │
│                                                                             │
│  Layer 2: API Gateway Cache (Edge)                                         │
│  ├── GET /api/parts/* - 15 min TTL                                         │
│  ├── GET /api/failure-cards/popular - 5 min TTL                            │
│  └── GET /api/garages/*/stats - 1 min TTL                                  │
│                                                                             │
│  Layer 3: Application Cache (Redis Cluster)                                │
│  ├── Session data - 24h TTL                                                │
│  ├── User permissions - 1h TTL                                             │
│  ├── Failure card embeddings - 6h TTL                                      │
│  ├── Parts pricing - 1h TTL                                                │
│  └── Garage configuration - 15 min TTL                                     │
│                                                                             │
│  Layer 4: Database Query Cache                                             │
│  ├── MongoDB: Frequent aggregations cached in Redis                        │
│  └── PostgreSQL: Materialized views for reports                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Cache Implementation:**
```python
class CacheManager:
    
    CACHE_POLICIES = {
        "failure_card": {
            "ttl": 3600,  # 1 hour
            "strategy": "write_through",
            "invalidation": ["on_update", "on_feedback"]
        },
        "parts_pricing": {
            "ttl": 900,  # 15 minutes
            "strategy": "cache_aside",
            "invalidation": ["scheduled_refresh"]
        },
        "user_session": {
            "ttl": 86400,  # 24 hours
            "strategy": "write_through",
            "invalidation": ["on_logout", "on_permission_change"]
        }
    }
    
    async def get_with_cache(self, key: str, fetch_fn, cache_type: str):
        policy = self.CACHE_POLICIES[cache_type]
        
        # Try cache first
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # Fetch from source
        data = await fetch_fn()
        
        # Store in cache
        await self.redis.setex(
            key, 
            policy["ttl"], 
            json.dumps(data)
        )
        
        return data
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

### 4.3 Load Distribution

```yaml
# Kubernetes HPA Configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: garage-operations-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: garage-operations
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 1000
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 4
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
```

### 4.4 Performance Targets

| Metric | Target | Critical Threshold | Measurement |
|--------|--------|-------------------|-------------|
| API Response Time (p50) | < 100ms | > 200ms | Prometheus |
| API Response Time (p99) | < 500ms | > 1000ms | Prometheus |
| Failure Card Match Time | < 300ms | > 800ms | Custom metric |
| Database Query Time (p95) | < 50ms | > 100ms | MongoDB profiler |
| Cache Hit Rate | > 85% | < 70% | Redis stats |
| Sync Latency (cross-location) | < 5s | > 30s | Custom metric |
| Throughput (tickets/min) | 500+ | < 200 | Load testing |

---

## 5. AI/ML Models

### 5.1 Model Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI/ML PIPELINE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    MODEL SERVING LAYER                               │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │  Symptom    │  │   Root      │  │  Solution   │  │  Anomaly    │ │   │
│  │  │  Classifier │  │   Cause     │  │  Ranker     │  │  Detector   │ │   │
│  │  │             │  │   Analyzer  │  │             │  │             │ │   │
│  │  │  BERT-based │  │  GPT-based  │  │  XGBoost +  │  │ Isolation   │ │   │
│  │  │  Multi-label│  │  RAG        │  │  Neural     │  │ Forest      │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                    ┌───────────────▼───────────────┐                       │
│                    │      Feature Store            │                       │
│                    │      (Feast/Redis)            │                       │
│                    └───────────────┬───────────────┘                       │
│                                    │                                        │
│  ┌─────────────────────────────────▼─────────────────────────────────┐     │
│  │                    TRAINING PIPELINE                               │     │
│  ├───────────────────────────────────────────────────────────────────┤     │
│  │                                                                     │     │
│  │  Raw Data → Preprocessing → Feature Engineering → Training → Eval │     │
│  │      │                                                          │   │     │
│  │      ▼                                                          ▼   │     │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────────┐  │     │
│  │  │Resolved │───▶│ Label   │───▶│ Feature │───▶│ Model Training  │  │     │
│  │  │Tickets  │    │Extraction│   │Transform│    │ (MLflow/Kubeflow│  │     │
│  │  └─────────┘    └─────────┘    └─────────┘    └─────────────────┘  │     │
│  │                                                                     │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Model Specifications

**Model 1: Symptom Classifier**
```python
class SymptomClassifier:
    """
    Multi-label classification of symptoms from technician description
    """
    
    architecture = "bert-base-uncased + classification head"
    input = "Free-text symptom description + vehicle context"
    output = "Multi-label symptom codes with confidence"
    
    training_data = {
        "source": "Resolved tickets with verified symptoms",
        "size": "50,000+ labeled examples",
        "split": "80/10/10 train/val/test",
        "augmentation": "Back-translation, synonym replacement"
    }
    
    features = [
        "symptom_text_embedding",  # 768-dim BERT
        "vehicle_make_encoded",     # One-hot
        "vehicle_model_encoded",    # One-hot
        "mileage_normalized",       # Float [0,1]
        "error_codes_multi_hot"     # Binary vector
    ]
    
    performance_targets = {
        "precision": 0.85,
        "recall": 0.80,
        "f1_score": 0.82
    }
```

**Model 2: Root Cause Analyzer (LLM-based)**
```python
class RootCauseAnalyzer:
    """
    RAG-based root cause analysis using LLM + failure card knowledge base
    """
    
    architecture = "GPT-4 with RAG (Retrieval Augmented Generation)"
    
    prompt_template = """
    You are an expert EV diagnostics engineer. Analyze the following failure:
    
    Vehicle: {vehicle_make} {vehicle_model} ({vehicle_year})
    Mileage: {mileage_km} km
    Symptoms: {symptoms}
    Error Codes: {error_codes}
    Technician Notes: {technician_notes}
    
    Similar Past Failures (from knowledge base):
    {retrieved_failure_cards}
    
    Provide:
    1. Most likely root cause (with confidence 0-1)
    2. Secondary possible causes
    3. Recommended diagnostic steps
    4. Reasoning for your conclusion
    
    Format as JSON.
    """
    
    retrieval_config = {
        "vector_db": "Pinecone",
        "embedding_model": "text-embedding-ada-002",
        "top_k": 5,
        "similarity_threshold": 0.7
    }
    
    guardrails = [
        "max_tokens: 1000",
        "temperature: 0.3",  # Low for consistency
        "confidence_calibration: enabled"
    ]
```

**Model 3: Solution Ranker**
```python
class SolutionRanker:
    """
    Rank potential solutions by relevance and effectiveness
    """
    
    architecture = "XGBoost ensemble + Neural reranker"
    
    features = {
        "semantic_similarity": "cosine(symptom_embedding, card_embedding)",
        "vehicle_match_score": "jaccard(vehicle_features)",
        "historical_success_rate": "card.success_confirmations / card.times_used",
        "recency_score": "exp(-days_since_creation / 365)",
        "complexity_match": "abs(ticket.severity - card.severity)",
        "parts_availability": "marketplace.check_availability(card.parts)"
    }
    
    training_approach = {
        "positive_labels": "Solution was used AND repair successful",
        "negative_labels": "Solution was shown but not used OR used but failed",
        "loss_function": "Pairwise ranking loss (LambdaRank)"
    }
    
    online_learning = {
        "enabled": True,
        "update_frequency": "daily",
        "feedback_signal": "technician_rating + repair_outcome"
    }
```

### 5.3 Training Data Pipeline

```python
class TrainingDataPipeline:
    """
    Continuous data collection and labeling for model improvement
    """
    
    async def generate_training_batch(self, date_range: DateRange):
        # Step 1: Extract resolved tickets
        tickets = await self.db.tickets.find({
            "status": "closed",
            "resolved_at": {"$gte": date_range.start, "$lte": date_range.end},
            "resolution_rating": {"$exists": True}
        })
        
        # Step 2: Link to failure cards used
        training_examples = []
        for ticket in tickets:
            example = {
                "input": {
                    "symptoms": ticket.symptoms,
                    "vehicle": ticket.vehicle_context,
                    "error_codes": ticket.error_codes
                },
                "output": {
                    "root_cause": ticket.verified_root_cause,
                    "solution_used": ticket.solution_applied,
                    "parts_used": ticket.parts_consumed
                },
                "label": {
                    "success": ticket.resolution_rating >= 4,
                    "first_time_fix": ticket.revisit_count == 0
                },
                "weight": self.calculate_example_weight(ticket)
            }
            training_examples.append(example)
        
        # Step 3: Balance dataset
        balanced = self.balance_classes(training_examples)
        
        # Step 4: Store in feature store
        await self.feature_store.ingest(balanced)
        
        return len(balanced)
    
    def calculate_example_weight(self, ticket):
        """
        Higher weight for:
        - Recent examples
        - Rare failure types
        - Expert-verified cases
        """
        recency_weight = math.exp(-ticket.age_days / 90)
        rarity_weight = 1 / math.log(ticket.failure_type_count + 1)
        expert_weight = 2.0 if ticket.verified_by_expert else 1.0
        
        return recency_weight * rarity_weight * expert_weight
```

### 5.4 Model Evaluation & Feedback

```python
class ModelEvaluator:
    """
    Continuous evaluation and A/B testing framework
    """
    
    metrics = {
        "symptom_classifier": [
            "precision@k", "recall@k", "f1_micro", "f1_macro"
        ],
        "root_cause_analyzer": [
            "accuracy_vs_expert", "confidence_calibration", "reasoning_quality"
        ],
        "solution_ranker": [
            "ndcg@5", "mrr", "first_time_fix_rate"
        ]
    }
    
    async def evaluate_model(self, model_name: str, test_set: Dataset):
        predictions = await self.model.predict(test_set.inputs)
        
        results = {}
        for metric_name in self.metrics[model_name]:
            metric_fn = getattr(self, f"calculate_{metric_name}")
            results[metric_name] = metric_fn(predictions, test_set.labels)
        
        # Log to MLflow
        mlflow.log_metrics(results)
        
        # Check regression
        if self.is_regression(results, model_name):
            await self.alert_team(f"Model regression detected: {model_name}")
        
        return results
    
    async def ab_test(self, model_a: str, model_b: str, traffic_split: float = 0.1):
        """
        Run A/B test between model versions
        """
        config = {
            "experiment_name": f"{model_a}_vs_{model_b}",
            "traffic_percentage_b": traffic_split,
            "min_samples": 1000,
            "significance_level": 0.05,
            "metrics_to_track": ["first_time_fix_rate", "technician_rating"]
        }
        
        await self.ab_service.create_experiment(config)
```

---

## 6. Data Synchronization

### 6.1 Sync Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED SYNC ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Garage A   │    │  Garage B   │    │  Garage C   │    │  Garage N   │  │
│  │  (Delhi)    │    │  (Mumbai)   │    │  (Chennai)  │    │  (...)      │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │         │
│         │                  │                  │                  │         │
│         ▼                  ▼                  ▼                  ▼         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SYNC SERVICE (Central)                            │   │
│  │                                                                       │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │   │
│  │  │  Change     │    │  Conflict   │    │  Broadcast  │              │   │
│  │  │  Detection  │───▶│  Resolution │───▶│  Engine     │              │   │
│  │  │             │    │             │    │             │              │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘              │   │
│  │         │                  │                  │                      │   │
│  │         ▼                  ▼                  ▼                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │              Event Log (Kafka / MongoDB Change Streams)      │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Sync Modes:                                                                │
│  • Real-time: Critical updates (new failure cards, urgent fixes)           │
│  • Near-real-time: Standard updates (5-second batches)                     │
│  • Scheduled: Non-critical (hourly analytics, reports)                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Conflict Resolution Strategy

```python
class ConflictResolver:
    """
    Handle conflicts when multiple locations update same data
    """
    
    RESOLUTION_STRATEGIES = {
        "failure_card": "merge_with_voting",
        "ticket": "last_write_wins",
        "inventory": "sum_quantities",
        "pricing": "source_of_truth"
    }
    
    async def resolve(self, entity_type: str, conflicts: List[ConflictRecord]):
        strategy = self.RESOLUTION_STRATEGIES[entity_type]
        
        if strategy == "merge_with_voting":
            return await self.merge_with_voting(conflicts)
        elif strategy == "last_write_wins":
            return await self.last_write_wins(conflicts)
        elif strategy == "sum_quantities":
            return await self.sum_quantities(conflicts)
        elif strategy == "source_of_truth":
            return await self.apply_source_of_truth(conflicts)
    
    async def merge_with_voting(self, conflicts: List[FailureCardConflict]):
        """
        For failure cards: Merge changes, use voting for conflicts
        """
        base_card = conflicts[0].base_version
        merged = base_card.copy()
        
        for field in ["root_cause", "solution_steps", "parts_required"]:
            field_values = [c.new_value.get(field) for c in conflicts]
            
            if len(set(str(v) for v in field_values)) == 1:
                # All agree - take the value
                merged[field] = field_values[0]
            else:
                # Conflict - use weighted voting
                merged[field] = self.weighted_vote(
                    values=field_values,
                    weights=[c.author_expertise_score for c in conflicts]
                )
        
        merged["version"] = base_card["version"] + 1
        merged["merge_metadata"] = {
            "sources": [c.source_garage for c in conflicts],
            "merged_at": datetime.utcnow().isoformat(),
            "conflicts_resolved": len(conflicts)
        }
        
        return merged
```

### 6.3 Offline Support & Edge Cases

```python
class OfflineSyncManager:
    """
    Handle technicians working without connectivity
    """
    
    async def queue_for_sync(self, operation: SyncOperation):
        """
        Queue operations when offline
        """
        await self.local_queue.push({
            "operation_id": str(uuid.uuid4()),
            "type": operation.type,
            "data": operation.data,
            "timestamp": datetime.utcnow().isoformat(),
            "garage_id": self.garage_id,
            "priority": operation.priority
        })
    
    async def sync_when_online(self):
        """
        Process queued operations when connectivity restored
        """
        while True:
            if not await self.network.is_online():
                await asyncio.sleep(5)
                continue
            
            pending = await self.local_queue.get_all()
            if not pending:
                await asyncio.sleep(5)
                continue
            
            # Sort by priority and timestamp
            sorted_ops = sorted(pending, key=lambda x: (x["priority"], x["timestamp"]))
            
            for op in sorted_ops:
                try:
                    # Check for conflicts
                    conflict = await self.check_conflict(op)
                    if conflict:
                        resolved = await self.conflict_resolver.resolve(op, conflict)
                        await self.sync_service.push(resolved)
                    else:
                        await self.sync_service.push(op)
                    
                    await self.local_queue.remove(op["operation_id"])
                    
                except SyncError as e:
                    logger.error(f"Sync failed for {op['operation_id']}: {e}")
                    await self.mark_for_retry(op)
    
    async def check_conflict(self, operation: dict) -> Optional[ConflictRecord]:
        """
        Check if remote has conflicting changes
        """
        if operation["type"] == "failure_card_update":
            remote_version = await self.sync_service.get_version(
                "failure_card", 
                operation["data"]["failure_card_id"]
            )
            local_version = operation["data"]["version"]
            
            if remote_version > local_version:
                return ConflictRecord(
                    local=operation,
                    remote=await self.sync_service.get(operation["data"]["failure_card_id"])
                )
        
        return None
```

### 6.4 Sync Performance Optimization

```python
class SyncOptimizer:
    """
    Optimize sync for network efficiency
    """
    
    async def delta_sync(self, entity_type: str, last_sync: datetime):
        """
        Only sync changes since last successful sync
        """
        changes = await self.change_log.get_changes(
            entity_type=entity_type,
            since=last_sync
        )
        
        # Compress changes
        compressed = self.compress_changes(changes)
        
        # Batch by priority
        batches = self.batch_by_priority(compressed)
        
        return batches
    
    def compress_changes(self, changes: List[Change]) -> List[Change]:
        """
        Remove redundant changes (e.g., multiple updates to same entity)
        """
        entity_changes = {}
        for change in changes:
            key = f"{change.entity_type}:{change.entity_id}"
            if key in entity_changes:
                # Keep only latest
                if change.timestamp > entity_changes[key].timestamp:
                    entity_changes[key] = change
            else:
                entity_changes[key] = change
        
        return list(entity_changes.values())
```

---

## 7. Security & Governance

### 7.1 Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SECURITY ARCHITECTURE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    AUTHENTICATION LAYER                              │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                       │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │   │
│  │  │   JWT       │    │   OAuth2    │    │   API Key   │              │   │
│  │  │   (Users)   │    │   (Google)  │    │   (M2M)     │              │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘              │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼─────────────────────────────────┐     │
│  │                    AUTHORIZATION LAYER (RBAC + ABAC)               │     │
│  ├───────────────────────────────────────────────────────────────────┤     │
│  │                                                                     │     │
│  │  Roles:                      Attributes:                           │     │
│  │  • admin                     • garage_id                           │     │
│  │  • manager                   • region                              │     │
│  │  • technician                • department                          │     │
│  │  • accountant                • shift                               │     │
│  │  • customer_support          • certification_level                 │     │
│  │                                                                     │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Permission Matrix

```python
PERMISSION_MATRIX = {
    "admin": {
        "tickets": ["create", "read", "update", "delete", "assign"],
        "failure_cards": ["create", "read", "update", "delete", "verify"],
        "employees": ["create", "read", "update", "delete"],
        "invoices": ["create", "read", "update", "delete", "void"],
        "reports": ["read", "export"],
        "settings": ["read", "update"],
        "all_garages": True
    },
    "manager": {
        "tickets": ["create", "read", "update", "assign"],
        "failure_cards": ["create", "read", "update", "verify"],
        "employees": ["read", "update"],
        "invoices": ["create", "read"],
        "reports": ["read", "export"],
        "settings": ["read"],
        "scope": "own_garage"
    },
    "technician": {
        "tickets": ["read", "update"],  # Only assigned tickets
        "failure_cards": ["create", "read"],
        "employees": [],
        "invoices": [],
        "reports": [],
        "settings": [],
        "scope": "assigned_only"
    },
    "accountant": {
        "tickets": ["read"],
        "failure_cards": [],
        "employees": ["read"],  # Salary info only
        "invoices": ["create", "read", "update"],
        "reports": ["read", "export"],
        "settings": [],
        "scope": "own_garage"
    },
    "customer_support": {
        "tickets": ["create", "read"],
        "failure_cards": ["read"],
        "employees": [],
        "invoices": ["read"],
        "reports": [],
        "settings": [],
        "scope": "own_garage"
    }
}
```

### 7.3 Data Encryption

```python
class SecurityManager:
    """
    Encryption and data protection
    """
    
    # Encryption at rest
    ENCRYPTION_CONFIG = {
        "database": {
            "mongodb": "AES-256-GCM (field-level for PII)",
            "postgresql": "TDE (Transparent Data Encryption)",
            "redis": "At-rest encryption enabled"
        },
        "storage": {
            "s3": "SSE-S3 with customer-managed keys",
            "backups": "AES-256 encrypted"
        }
    }
    
    # Fields requiring encryption
    PII_FIELDS = [
        "customer.aadhaar_number",
        "customer.pan_number",
        "employee.bank_account_number",
        "employee.aadhaar_number",
        "employee.pan_number",
        "invoice.customer_gstin"
    ]
    
    def encrypt_pii(self, document: dict) -> dict:
        """Encrypt PII fields before storage"""
        encrypted = document.copy()
        for field_path in self.PII_FIELDS:
            value = self.get_nested(encrypted, field_path)
            if value:
                encrypted_value = self.kms.encrypt(value)
                self.set_nested(encrypted, field_path, encrypted_value)
        return encrypted
    
    def decrypt_pii(self, document: dict, user_permissions: List[str]) -> dict:
        """Decrypt PII fields based on user permissions"""
        decrypted = document.copy()
        for field_path in self.PII_FIELDS:
            if self.can_access_field(field_path, user_permissions):
                encrypted_value = self.get_nested(decrypted, field_path)
                if encrypted_value:
                    decrypted_value = self.kms.decrypt(encrypted_value)
                    self.set_nested(decrypted, field_path, decrypted_value)
            else:
                # Mask the field
                self.set_nested(decrypted, field_path, "****MASKED****")
        return decrypted
```

### 7.4 Audit Trail

```python
class AuditLogger:
    """
    Comprehensive audit logging for compliance
    """
    
    AUDIT_EVENTS = [
        "user.login",
        "user.logout",
        "user.permission_change",
        "ticket.create",
        "ticket.update",
        "ticket.delete",
        "failure_card.create",
        "failure_card.verify",
        "invoice.create",
        "invoice.void",
        "employee.salary_view",
        "employee.pii_access",
        "report.export",
        "settings.change"
    ]
    
    async def log(self, event: str, context: dict):
        audit_record = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event,
            "user_id": context.get("user_id"),
            "user_role": context.get("user_role"),
            "garage_id": context.get("garage_id"),
            "ip_address": context.get("ip_address"),
            "user_agent": context.get("user_agent"),
            "resource_type": context.get("resource_type"),
            "resource_id": context.get("resource_id"),
            "action": context.get("action"),
            "old_value": context.get("old_value"),  # For updates
            "new_value": context.get("new_value"),
            "result": context.get("result", "success")
        }
        
        # Write to immutable audit log
        await self.audit_db.insert_one(audit_record)
        
        # Alert on suspicious activity
        if await self.is_suspicious(audit_record):
            await self.alert_security_team(audit_record)
    
    async def is_suspicious(self, record: dict) -> bool:
        """Detect anomalous access patterns"""
        # Multiple failed logins
        if record["event_type"] == "user.login" and record["result"] == "failure":
            recent_failures = await self.count_recent_failures(
                record["user_id"], 
                minutes=15
            )
            if recent_failures > 5:
                return True
        
        # Bulk data export
        if record["event_type"] == "report.export":
            recent_exports = await self.count_recent_exports(
                record["user_id"],
                minutes=60
            )
            if recent_exports > 10:
                return True
        
        # Off-hours access to sensitive data
        if record["event_type"] == "employee.pii_access":
            if not self.is_business_hours(record["timestamp"]):
                return True
        
        return False
```

---

## 8. Continuous Improvement Feedback Loops

### 8.1 Feedback Collection Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                                                       │
│  │   Technician    │                                                       │
│  │   Interaction   │                                                       │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FEEDBACK COLLECTION                               │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │  Explicit   │  │  Implicit   │  │  Outcome    │  │  Timing     │ │   │
│  │  │  Feedback   │  │  Feedback   │  │  Feedback   │  │  Feedback   │ │   │
│  │  │             │  │             │  │             │  │             │ │   │
│  │  │ • Rating    │  │ • Click     │  │ • First-fix │  │ • Resolution│ │   │
│  │  │ • Comment   │  │ • Dwell time│  │ • Revisit   │  │   time      │ │   │
│  │  │ • Correction│  │ • Selection │  │ • Customer  │  │ • Parts     │ │   │
│  │  │             │  │   order     │  │   rating    │  │   accuracy  │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  │                                                                       │   │
│  └──────────────────────────────┬────────────────────────────────────────┘   │
│                                 │                                            │
│                                 ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FEEDBACK PROCESSING                               │   │
│  │                                                                       │   │
│  │  1. Aggregation     → Group by failure card, vehicle, symptom       │   │
│  │  2. Normalization   → Adjust for technician experience level        │   │
│  │  3. Weighting       → Recent feedback weighted higher               │   │
│  │  4. Anomaly Filter  → Remove outliers                               │   │
│  │                                                                       │   │
│  └──────────────────────────────┬────────────────────────────────────────┘   │
│                                 │                                            │
│                                 ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    MODEL UPDATE TRIGGERS                             │   │
│  │                                                                       │   │
│  │  • Failure card effectiveness score update                          │   │
│  │  • Ranker model retraining (weekly)                                 │   │
│  │  • Classifier fine-tuning (monthly)                                 │   │
│  │  • Knowledge base expansion (continuous)                            │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Effectiveness Metrics

```python
class EffectivenessTracker:
    """
    Track and update failure card effectiveness
    """
    
    METRICS = {
        "first_time_fix_rate": {
            "description": "% of repairs resolved without revisit",
            "calculation": "successful_fixes / total_uses",
            "target": 0.90,
            "weight": 0.35
        },
        "technician_acceptance_rate": {
            "description": "% of times suggestion was used",
            "calculation": "times_used / times_shown",
            "target": 0.70,
            "weight": 0.20
        },
        "average_rating": {
            "description": "Average technician rating (1-5)",
            "calculation": "sum(ratings) / count(ratings)",
            "target": 4.0,
            "weight": 0.25
        },
        "time_to_resolution": {
            "description": "Average repair time vs estimate",
            "calculation": "actual_time / estimated_time",
            "target": 1.0,
            "weight": 0.20
        }
    }
    
    async def update_effectiveness(self, card_id: str, feedback: FeedbackEvent):
        card = await self.db.failure_cards.find_one({"failure_card_id": card_id})
        
        # Update raw metrics
        stats = card.get("usage_statistics", {})
        
        if feedback.type == "used_as_solution":
            stats["times_used_as_solution"] = stats.get("times_used_as_solution", 0) + 1
        
        if feedback.type == "repair_outcome":
            if feedback.success:
                stats["success_confirmations"] = stats.get("success_confirmations", 0) + 1
            else:
                stats["failure_reports"] = stats.get("failure_reports", 0) + 1
        
        if feedback.type == "rating":
            ratings = stats.get("ratings", [])
            ratings.append(feedback.value)
            stats["ratings"] = ratings[-100]  # Keep last 100 ratings
        
        # Calculate composite effectiveness score
        effectiveness = self.calculate_effectiveness(stats)
        stats["effectiveness_score"] = effectiveness
        
        # Update card
        await self.db.failure_cards.update_one(
            {"failure_card_id": card_id},
            {"$set": {"usage_statistics": stats}}
        )
        
        # Trigger alerts if effectiveness drops
        if effectiveness < 0.5 and stats.get("times_matched", 0) > 20:
            await self.alert_for_review(card_id, "low_effectiveness")
    
    def calculate_effectiveness(self, stats: dict) -> float:
        scores = {}
        
        # First time fix rate
        total_uses = stats.get("times_used_as_solution", 0)
        if total_uses > 0:
            successes = stats.get("success_confirmations", 0)
            scores["first_time_fix_rate"] = successes / total_uses
        
        # Acceptance rate
        times_shown = stats.get("times_matched", 0)
        if times_shown > 0:
            scores["technician_acceptance_rate"] = total_uses / times_shown
        
        # Average rating
        ratings = stats.get("ratings", [])
        if ratings:
            scores["average_rating"] = sum(ratings) / len(ratings) / 5  # Normalize to 0-1
        
        # Weighted average
        total_weight = 0
        weighted_sum = 0
        for metric, config in self.METRICS.items():
            if metric in scores:
                weighted_sum += scores[metric] * config["weight"]
                total_weight += config["weight"]
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
```

### 8.3 System Intelligence Metrics

```python
class IntelligenceMetrics:
    """
    Track how smart the system is getting over time
    """
    
    async def generate_intelligence_report(self, period: str = "monthly"):
        report = {
            "period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": {}
        }
        
        # 1. Knowledge Base Growth
        report["metrics"]["knowledge_base"] = {
            "total_failure_cards": await self.count_failure_cards(),
            "new_cards_period": await self.count_new_cards(period),
            "verified_cards_ratio": await self.verified_ratio(),
            "coverage_by_vehicle": await self.coverage_by_vehicle_type()
        }
        
        # 2. Matching Accuracy
        report["metrics"]["matching_accuracy"] = {
            "avg_position_of_used_solution": await self.avg_rank_of_used(),
            "first_suggestion_acceptance_rate": await self.first_suggestion_rate(),
            "no_match_found_rate": await self.no_match_rate()
        }
        
        # 3. Repair Efficiency
        report["metrics"]["repair_efficiency"] = {
            "first_time_fix_rate": await self.global_ftfr(),
            "avg_resolution_time": await self.avg_resolution_time(),
            "parts_accuracy": await self.parts_prediction_accuracy()
        }
        
        # 4. Network Effect
        report["metrics"]["network_effect"] = {
            "cross_location_solution_usage": await self.cross_location_usage(),
            "time_to_network_propagation": await self.avg_propagation_time(),
            "solutions_discovered_vs_propagated": await self.discovery_ratio()
        }
        
        # 5. Model Performance
        report["metrics"]["model_performance"] = {
            "symptom_classifier_f1": await self.get_model_metric("symptom_classifier", "f1"),
            "root_cause_accuracy": await self.get_model_metric("root_cause", "accuracy"),
            "ranker_ndcg": await self.get_model_metric("ranker", "ndcg@5")
        }
        
        return report
    
    async def trend_analysis(self, metric: str, periods: int = 6):
        """Show improvement trend over time"""
        trends = []
        for i in range(periods):
            period_data = await self.get_metric_for_period(metric, i)
            trends.append(period_data)
        
        improvement = (trends[-1] - trends[0]) / trends[0] * 100
        return {
            "metric": metric,
            "values": trends,
            "improvement_percentage": improvement,
            "trend": "improving" if improvement > 0 else "declining"
        }
```

---

## 9. Operational Considerations

### 9.1 Deployment Strategy

```yaml
# Kubernetes Deployment Configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: battwheels-api
  labels:
    app: battwheels
    component: api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: battwheels
      component: api
  template:
    metadata:
      labels:
        app: battwheels
        component: api
    spec:
      containers:
      - name: api
        image: battwheels/api:${VERSION}
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: MONGO_URL
          valueFrom:
            secretKeyRef:
              name: battwheels-secrets
              key: mongo-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: battwheels-secrets
              key: redis-url
```

### 9.2 Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  Metrics    │    │   Logs      │    │   Traces    │                     │
│  │ (Prometheus)│    │ (Loki/ELK)  │    │  (Jaeger)   │                     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│         │                  │                  │                             │
│         └──────────────────┼──────────────────┘                             │
│                            │                                                │
│                   ┌────────▼────────┐                                       │
│                   │    Grafana      │                                       │
│                   │   Dashboards    │                                       │
│                   └────────┬────────┘                                       │
│                            │                                                │
│         ┌──────────────────┼──────────────────┐                             │
│         │                  │                  │                             │
│         ▼                  ▼                  ▼                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  Alerting   │    │  SLO        │    │  Business   │                     │
│  │ (PagerDuty) │    │  Tracking   │    │  Metrics    │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Dashboards:**
1. **System Health:** CPU, Memory, Network, Error rates
2. **Business KPIs:** Tickets/day, Resolution time, First-fix rate
3. **AI Performance:** Match accuracy, Model latency, Training metrics
4. **Sync Health:** Lag time, Conflict rate, Offline queue depth

### 9.3 Disaster Recovery

```python
class DisasterRecoveryPlan:
    """
    DR procedures for Battwheels OS
    """
    
    RTO = "4 hours"  # Recovery Time Objective
    RPO = "1 hour"   # Recovery Point Objective
    
    BACKUP_STRATEGY = {
        "mongodb": {
            "type": "continuous_backup",
            "provider": "MongoDB Atlas",
            "retention": "30 days",
            "point_in_time_recovery": True
        },
        "postgresql": {
            "type": "pg_dump + WAL archiving",
            "frequency": "hourly",
            "retention": "7 days",
            "cross_region_replication": True
        },
        "redis": {
            "type": "RDB + AOF",
            "frequency": "every 5 minutes",
            "retention": "24 hours"
        },
        "s3": {
            "type": "cross_region_replication",
            "versioning": True,
            "retention": "90 days"
        }
    }
    
    FAILOVER_PROCEDURES = {
        "database_failure": [
            "1. Detect failure via health checks (< 30 seconds)",
            "2. Promote replica to primary",
            "3. Update connection strings via config server",
            "4. Notify ops team",
            "5. Investigate root cause"
        ],
        "region_failure": [
            "1. Detect via multi-region health checks",
            "2. Update DNS to point to DR region",
            "3. Promote DR database replicas",
            "4. Scale up DR compute resources",
            "5. Notify all garage locations"
        ],
        "data_corruption": [
            "1. Identify corruption scope",
            "2. Isolate affected services",
            "3. Restore from point-in-time backup",
            "4. Replay transaction logs",
            "5. Validate data integrity",
            "6. Resume services"
        ]
    }
```

### 9.4 Rollback Procedures

```python
class RollbackManager:
    """
    Safe rollback procedures for deployments
    """
    
    async def rollback_deployment(self, service: str, reason: str):
        # 1. Log rollback initiation
        await self.audit_log.log("rollback.initiated", {
            "service": service,
            "reason": reason,
            "initiated_by": self.current_user
        })
        
        # 2. Get previous stable version
        previous_version = await self.get_previous_stable_version(service)
        
        # 3. Execute rollback
        if service == "api":
            await self.kubernetes.rollout_undo(f"deployment/{service}")
        elif service == "database_migration":
            await self.run_migration_rollback(previous_version)
        elif service == "ml_model":
            await self.revert_model_version(service, previous_version)
        
        # 4. Verify rollback success
        health_check = await self.verify_service_health(service)
        
        # 5. Notify team
        await self.notify_team({
            "type": "rollback_complete",
            "service": service,
            "from_version": self.current_version,
            "to_version": previous_version,
            "health_check": health_check
        })
        
        return {
            "success": health_check.passed,
            "previous_version": previous_version,
            "rollback_time": datetime.utcnow().isoformat()
        }
```

---

## 10. Implementation Roadmap

### 10.1 Phase 1: Foundation (Weeks 1-4)

| Task | Description | Dependencies |
|------|-------------|--------------|
| Backend Refactoring | Split monolithic server.py into microservices | None |
| Invoice Service | PDF generation with GST compliance | Backend refactoring |
| Notification Service | Email + WhatsApp integration | Backend refactoring |
| Database Optimization | Indexing, sharding setup | None |

### 10.2 Phase 2: Intelligence Engine (Weeks 5-8)

| Task | Description | Dependencies |
|------|-------------|--------------|
| Failure Card Schema | Implement full card structure | Phase 1 |
| Vector Database Setup | Pinecone/Weaviate integration | Phase 1 |
| Symptom Classifier | Train and deploy v1 | Failure Card Schema |
| Matching Engine | Implement multi-stage matching | Vector DB, Classifier |

### 10.3 Phase 3: Network Sync (Weeks 9-12)

| Task | Description | Dependencies |
|------|-------------|--------------|
| Event Bus Setup | RabbitMQ/Kafka infrastructure | Phase 1 |
| Sync Service | Cross-location synchronization | Event Bus |
| Offline Support | Queue-based offline handling | Sync Service |
| Conflict Resolution | Implement merge strategies | Sync Service |

### 10.4 Phase 4: AI Enhancement (Weeks 13-16)

| Task | Description | Dependencies |
|------|-------------|--------------|
| Root Cause Analyzer | LLM-based analysis with RAG | Phase 2 |
| Solution Ranker | ML ranking model | Phase 2 |
| Feedback System | Collection and processing | Phase 2 |
| Model Training Pipeline | Automated retraining | Feedback System |

### 10.5 Phase 5: Production Hardening (Weeks 17-20)

| Task | Description | Dependencies |
|------|-------------|--------------|
| Security Audit | Penetration testing, compliance | All phases |
| Performance Testing | Load testing, optimization | All phases |
| DR Setup | Backup, failover procedures | All phases |
| Monitoring | Full observability stack | All phases |

---

## Appendix A: Technology Stack Summary

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | React 19, Tailwind, Shadcn/UI | Modern, component-based UI |
| **API Gateway** | Kong / Nginx | Rate limiting, auth, routing |
| **Backend** | FastAPI (Python) | Async, fast, ML-friendly |
| **Primary Database** | MongoDB Atlas | Flexible schema, horizontal scale |
| **Relational Database** | PostgreSQL | ACID for financial data |
| **Cache** | Redis Cluster | Session, caching, pub/sub |
| **Message Queue** | RabbitMQ / Kafka | Event-driven architecture |
| **Vector Database** | Pinecone / Weaviate | Semantic search |
| **ML Platform** | MLflow + Kubeflow | Model lifecycle management |
| **Object Storage** | S3 / MinIO | Documents, images, models |
| **Container Orchestration** | Kubernetes | Scalability, reliability |
| **Monitoring** | Prometheus + Grafana | Metrics, alerting |
| **Logging** | Loki / ELK | Centralized logging |
| **Tracing** | Jaeger | Distributed tracing |

---

## Appendix B: API Versioning Strategy

```
Base URL: https://api.battwheels.com/v1/

Versioning Policy:
- Major versions (v1, v2) for breaking changes
- Minor versions via header: X-API-Version: 1.2
- Deprecation notice: 6 months before removal
- Sunset header for deprecated endpoints
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-16 | Architecture Team | Initial specification |

---

*This document serves as the authoritative technical specification for Battwheels OS. All development should align with the architecture and patterns defined herein. Deviations require architectural review and approval.*
