---
name: "speckit-constitution-plus"
description: "Ejecuta la fase constitution base y, si termina exitosamente, ofrece de forma opcional el especificador de agentes del proyecto. Usar cuando el usuario invoca /speckit-constitution-plus."
argument-hint: "Principles or values for the project constitution"
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "gen_speckit"
user-invocable: true
disable-model-invocation: false
---

## Pasos

1. Ejecutar la skill existente `/speckit-constitution` pasando exactamente los mismos argumentos recibidos. No modificarla ni reimplementar su comportamiento.
2. Solo si la fase constitution termina exitosamente, ofrecer al usuario ejecutar opcionalmente `/speckit-agents` para especificar los agentes del proyecto. La oferta no debe bloquear el flujo; si el usuario declina, terminar sin ningún efecto secundario.
