# fly-in
Fly-in free, feel the ecstasy :)
# Simulación de navegación de drones

## Idea general

El proyecto simula uno o varios drones desplazándose por una red de zonas conectadas.

Cada dron parte de una zona inicial, tiene un destino y debe recorrer la red respetando las restricciones de capacidad tanto de las zonas como de las conexiones.

El sistema avanza por turnos. En cada turno cada dron analiza su situación, intenta avanzar y actualiza el estado global de la simulación.

---

## Modelo conceptual

```text
                 RED DE NAVEGACIÓN

              +--------------------+
              |      Zona A        |
              +--------------------+
                    │
          capacidad │
                    │
              +--------------------+
              |      Zona B        |
              +--------------------+
                    │
                    │
              +--------------------+
              |      Zona C        |
              +--------------------+

Cada zona conoce:

• cuántos drones admite
• cuántos drones contiene
• su tipo (normal, restringida, prioridad...)
```

Las conexiones representan los caminos que pueden recorrer los drones y también tienen un límite de capacidad.

---

## Ciclo de vida de un dron

```text
            Crear dron
                │
                ▼
      Colocar en zona inicial
                │
                ▼
       Calcular ruta objetivo
                │
                ▼
      Esperar al siguiente turno
```

A partir de ese momento el dron participa en cada iteración de la simulación.

---

## Comportamiento durante un turno

```text
                   NUEVO TURNO
                        │
                        ▼
                        
              ¿Tiene destino pendiente?
                  │             │
               No │             │ Sí
                  ▼             ▼
              Finalizado   Obtener siguiente zona

                                   │
                                   ▼

                     ¿La conexión tiene capacidad?
                          │                │
                       No │                │ Sí
                          ▼                ▼
                      Esperar      ¿La zona admite otro dron?
                      
                                         │
                                _________|
                               │         │
                               No        Sí
                               │         │
                               ▼         ▼
                          ▶️ Avanzo    ⏸️ Espero
        
                                         │
                                         ▼
                             Actualizar ocupaciones
                            
                                         │
                                         ▼
                            ¿Destino alcanzado?
                               │            │
                            No │            │ Sí
                               │            ▼
                               └──────► Entregado
```

---

## Vista desde el dron

```text
🚁 Estoy en la [zona A]
        │
        ▼
¿Cuál es mi siguiente zona?
        │
        ▼
¿La conexión está libre?
        │
        ▼
¿La zona tiene espacio?
        │
   ┌────┴────┐
   │         │
  Sí         No
   │         │
   ▼         ▼
 ▶️ Avanzo  ⏸️ Espero
   │
   ▼
Actualizar estado
   │
   ▼
¿He llegado?
   │
   └────────────► repetir en el siguiente turno
```

---

## Estado global de la simulación

Durante toda la ejecución existe un estado compartido que mantiene la información de la simulación.

```text
                  Simulation State
        ┌────────────────────────────────┐
        │ Turno actual                   │
        │                                │
        │ Drones                         │
        │                                │
        │ Ocupación de zonas             │
        │                                │
        │ Ocupación de conexiones        │
        │                                │
        │ Drones entregados              │
        │                                │
        │ Movimientos del turno          │
        └────────────────────────────────┘
```

Cada movimiento realizado por un dron modifica este estado, que será utilizado en el siguiente turno.

---

## Filosofía

El proyecto no pretende mover un único dron de principio a fin, sino simular un sistema donde varios drones comparten una misma red y compiten por recursos limitados.

Las decisiones de movimiento dependen tanto de la ruta planificada como del estado dinámico de la simulación (ocupación de zonas y conexiones), haciendo que cada turno pueda producir esperas, bloqueos o avances hasta completar todas las entregas.