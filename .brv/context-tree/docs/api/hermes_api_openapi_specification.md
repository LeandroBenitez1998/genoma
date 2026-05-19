---
title: Hermes API OpenAPI Specification
summary: Complete OpenAPI 3.0 specification defining all Hermes backend endpoints including job management, skills, evolution, and WebSocket streaming
tags: []
related: []
keywords: []
createdAt: '2026-04-28T03:39:56.018Z'
updatedAt: '2026-04-28T03:46:41.133Z'
---
## Reason
Preserving complete OpenAPI 3.0 spec for Hermes backend API

## Raw Concept
**Task:**
Document Hermes backend API specification

**Files:**
- docs/api/hermes-api.openapi.yaml

**Timestamp:** 2026-04-28

## Narrative
### Structure
OpenAPI 3.0 specification with paths for /jobs, /skills, /evolve, /config, and WebSocket /ws endpoint

---


openapi: &quot;3.1.0&quot;
info:
  title: Hermes Agent API
  description: |
    API del backend de Hermes (FastAPI/Python) expuesta por el gateway de hermes-cli.
    El frontend Next.js consume estos endpoints y espera este contrato de respuesta.
  version: &quot;1.0.0&quot;
  contact:
    name: Hermes Dashboard

servers:
  - url: &quot;http://127.0.0.1:8000&quot;
    description: Backend local (default). NEXT_PUBLIC_API_BASE sobreescribe esta URL.

paths:
  ## ── Skills ──────────────────────────────────────────────────────────
  /api/skills:
    get:
      operationId: listSkills
      summary: Listar todos los skills instalados
      description: Retorna la lista completa de skills detectados en los directorios configurados.
      responses:
        &quot;200&quot;:
          description: Lista de skills
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: &quot;#/components/schemas/SkillInfo&quot;
        &quot;503&quot;:
          $ref: &quot;#/components/responses/ServiceUnavailable&quot;

  /api/skills/{name}:
    get:
      operationId: getSkill
      summary: Obtener detalle de un skill
      description: Retorna el contenido completo de un skill incluyendo frontmatter y body.
      parameters:
        - name: name
          in: path
          required: true
          schema:
            type: string
      responses:
        &quot;200&quot;:
          description: Detalle del skill
          content:
            application/json:
              schema:
                $ref: &quot;#/components/schemas/SkillDetail&quot;
        &quot;503&quot;:
          $ref: &quot;#/components/responses/ServiceUnavailable&quot;

  /api/skills/{name}/evolution-history:
    get:
      operationId: getSkillHistory
      summary: Historial de evolución de un skill
      parameters:
        - name: name
          in: path
          required: true
          schema:
            type: string
      responses:
        &quot;200&quot;:
          description: Lista de ejecuciones de evolución para este skill
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: &quot;#/components/schemas/EvolutionRun&quot;
        &quot;503&quot;:
          $ref: &quot;#/components/responses/ServiceUnavailable&quot;

  ## ── Evolution ───────────────────────────────────────────────────────
  /api/evolution/runs:
    get:
      operationId: listEvolutionRuns
      summary: Listar todas las ejecuciones de evolución
      description: Retorna el historial completo de ejecuciones de evolución.
      responses:
        &quot;200&quot;:
          description: Lista de runs de evolución
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: &quot;#/components/schemas/EvolutionRun&quot;
        &quot;503&quot;:
          $ref: &quot;#/components/responses/ServiceUnavailable&quot;

  /api/evolution/start:
    post:
      operationId: startEvolution
      summary: Iniciar una evolución
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [skill_name, iterations]
              properties:
                skill_name:
                  type: string
                  description: Nombre del skill a evolucionar
                iterations:
                  type: integer
                  minimum: 1
                  maximum: 20
                  default: 3
                eval_source:
                  type: string
                  default: synthetic
      responses:
        &quot;200&quot;:
          description: Job de evolución creado
          content:
            application/json:
              schema:
                type: object
                properties:
                  job_id:
                    type: string
                  skill:
                    type: string
                  status:
                    type: string
                  error:
                    type: string
        &quot;503&quot;:
          $ref: &quot;#/components/responses/ServiceUnavailable&quot;

  ## ── Jobs ───────────────────────────────────────────────────────────
  /api/jobs:
    get:
      operationId: listJobs
      summary: Listar jobs activos o todos
      parameters:
        - name: active_only
          in: query
          schema:
            type: boolean
            default: false
      responses:
        &quot;200&quot;:
          description: Lista de jobs
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: &quot;#/components/schemas/EvolutionJob&quot;
        &quot;503&quot;:
          $ref: &quot;#/components/responses/ServiceUnavailable&quot;

  /api/jobs/{jobId}:
    get:
      operationId: getJob
      summary: Obtener detalle de un job
      parameters:
        - name: jobId
          in: path
          required: true
          schema:
            type: string
      responses:
        &quot;200&quot;:
          description: Detalle del job
          content:
            application/json:
              schema:
                $ref: &quot;#/components/schemas/EvolutionJob&quot;
        &quot;503&quot;:
          $ref: &quot;#/components/responses/ServiceUnavailable&quot;
    delete:
      operationId: cancelJob
      summary: Cancelar un job activo
      parameters:
        - name: jobId
          in: path
          required: true
          schema:
            type: string
      responses:
        &quot;200&quot;:
          description: Job cancelado
        &quot;503&quot;:
          $ref: &quot;#/components/responses/ServiceUnavailable&quot;

  /api/jobs/{jobId}/logs:
    get:
      operationId: getJobLogs
      summary: Obtener logs de un job
      parameters:
        - name: jobId
          in: path
          required: true
          schema:
            type: string
        - name: since
          in: query
          schema:
            type: integer
            default: 0
      responses:
        &quot;200&quot;:
          description: Logs del job (streaming paginado)
          content:
            application/json:
              schema:
                type: object
                properties:
                  job_id:
                    type: string
                  total_lines:
                    type: integer
                  logs:
                    type: array
                    items:
                      type: string
                  status:
                    type: string
                  progress:
                    type: number
        &quot;503&quot;:
          $ref: &quot;#/components/responses/ServiceUnavailable&quot;

  ## ── Health ─────────────────────────────────────────────────────────
  /api/health:
    get:
      operationId: healthCheck
      summary: Health check del backend
      responses:
        &quot;200&quot;:
          description: Estado del sistema
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: ok
                  hermes_repo:
                    type: string
                  hermes_repo_exists:
                    type: boolean
                  evolution_dir:
                    type: string
                  evolution_dir_exists:
                    type: boolean
                  skills_count:
                    type: integer
                  categories:
                    type: object
                    additionalProperties:
                      type: integer
        &quot;503&quot;:
          $ref: &quot;#/components/responses/ServiceUnavailable&quot;

## ── Componentes ─────────────────────────────────────────────────────
components:
  schemas:
    SkillInfo:
      type: object
      required: [name, path, description, size, last_modified, providers, provider_count, category]
      properties:
        name:
          type: string
          example: accessibility
        path:
          type: string
          example: /home/user/.agents/skills/accessibility
        description:
          type: string
        size:
          type: number
        last_modified:
          type: string
          format: date-time
        providers:
          type: array
          items:
            type: string
        provider_count:
          type: integer
        category:
          type: string

    SkillDetail:
      type: object
      required: [name, path, frontmatter, body, raw, size]
      properties:
        name:
          type: string
        path:
          type: string
        frontmatter:
          type: object
          additionalProperties: true
          description: YAML frontmatter parseado
        body:
          type: string
          description: Contenido Markdown sin frontmatter
        raw:
          type: string
          description: Archivo completo sin procesar
        size:
          type: number

    EvolutionRun:
      type: object
      required:
        [skill_name, timestamp, baseline_score, evolved_score, improvement,
         elapsed_seconds, constraints_passed, iterations, optimizer_model]
      properties:
        skill_name:
          type: string
        timestamp:
          type: string
        baseline_score:
          type: number
          description: Score pre-evolución (0-1)
        evolved_score:
          type: number
          description: Score post-evolución (0-1)
        improvement:
          type: number
          description: Diferencia (positivo = mejoró)
        elapsed_seconds:
          type: number
        constraints_passed:
          type: boolean
        iterations:
          type: integer
        optimizer_model:
          type: string

    EvolutionJob:
      type: object
      properties:
        id:
          type: string
        skill_name:
          type: string
        status:
          type: string
          enum:
            [queued, loading_skill, building_dataset, validating,
             configuring, optimizing, evaluating, saving, completed, failed]
        iterations:
          type: integer
        current_iteration:
          type: integer
        pid:
          type: integer
          nullable: true
        started_at:
          type: string
        completed_at:
          type: string
        baseline_score:
          type: number
          nullable: true
        current_best_score:
          type: number
          nullable: true
        evolved_score:
          type: number
          nullable: true
        improvement:
          type: number
          nullable: true
        error:
          type: string
        progress:
          type: number
        logs:
          type: array
          items:
            type: string

    ## ── Error tipado ─────────────────────────────────────────────────
    ApiError:
      type: object
      description: |
        Contrato de error que el frontend debe interpretar.
        Cualquier respuesta != 2xx o error de red se mapea a esta estructura.
      required: [kind, message]
      properties:
        kind:
          type: string
          enum: [network, timeout, server, client]
          description: |
            network  → fetch() rechazó (servicio no alcanzable)
            timeout  → AbortController superó el límite
            server   → HTTP 5xx
            client   → HTTP 4xx
        message:
          type: string
          description: Texto legible para UI
        status:
          type: integer
          description: Código HTTP (solo en server y client)
        endpoint:
          type: string
          description: Ruta que falló (para diagnóstico)

    ## ── Health fallback ──────────────────────────────────────────────
    HealthStatus:
      type: object
      properties:
        status:
          type: string
          enum: [ok, disconnected]
        lastSeen:
          type: string
          format: date-time
          description: Última vez que /api/health respondió 200

  ## ── Respuesta 503 estandarizada ───────────────────────────────────
  responses:
    ServiceUnavailable:
      description: &gt;
        El backend no está alcanzable. El frontend debe interpretar esto como señal
        para mostrar estado &quot;Desconectado&quot; con opción de reintento.
      content:
        application/json:
          schema:
            $ref: &quot;#/components/schemas/ApiError&quot;
          example:
            kind: network
            message: &quot;El servicio de Hermes no está disponible&quot;
            endpoint: &quot;/api/skills&quot;

    
