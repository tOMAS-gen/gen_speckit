# Contract: definición portable de agente

**Feature**: 002-agent-specifier

Contrato entre `speckit-agents` (productor), el usuario (editor con prioridad) y
cualquier CLI principal (consumidor).

## Archivo portable — `.specify/agents/<nombre>.md`

```markdown
---
name: revisor-seguridad
dominio: seguridad
rol: Auditar cambios sensibles y configuraciones ante riesgos de seguridad
origen: generado
fecha: 2026-07-18
---

## Responsabilidades

- Revisar diffs que toquen autenticación, permisos, secretos o entrada de usuarios
- Mantener una lista de patrones de riesgo del proyecto

## Límites

- No implementa features; solo audita y reporta
- No aprueba su propio trabajo

## Instrucciones

Sos el agente de seguridad del proyecto. Cuando se te invoque con un cambio o
diseño, evaluá superficies de ataque, manejo de secretos y validación de entradas.
Reportá hallazgos con severidad y sugerencia concreta.
```

**Reglas del productor** (`speckit-agents`):
1. Nombre de archivo = `name` del frontmatter (kebab-case, único).
2. NUNCA sobrescribir un archivo existente; solo crear faltantes.
3. Escribir solo tras confirmación explícita del usuario (FR-003).
4. Idioma del contenido = idioma del proyecto (R5).

**Reglas del consumidor** (cualquier CLI):
- La cobertura de un dominio se decide por el campo `dominio` del frontmatter, no
  por el nombre del archivo ni del agente.
- Un archivo ilegible (sin frontmatter parseable) se reporta como inválido y se trata
  como NO cobertura (el dominio puede recibir propuesta nueva con otro nombre).

## Derivación nativa Claude — `.claude/agents/<nombre>.md`

```markdown
---
name: revisor-seguridad
description: Auditar cambios sensibles y configuraciones ante riesgos de seguridad (dominio seguridad). Usar proactivamente en cambios de auth, permisos o secretos.
---

<Instrucciones + Responsabilidades + Límites del portable, como system prompt>
```

- Se genera solo junto con el portable (misma corrida aprobada).
- Si el CLI principal no es Claude, este paso se omite sin error (el portable es el
  consumible universal).
