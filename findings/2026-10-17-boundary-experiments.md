# Dio Boundary Lab — Findings, 2026-10-17

## Method
Treat capability claims as conditional hypotheses. Record the tool state, authorization, connectivity, account tier, context, and observed result. A failed test establishes only failure under those conditions; a successful test establishes a demonstrated door, not permanent availability.

## Findings

1. **Boundaries are conditional, not binary.** “Can/can’t” repeatedly decomposed into available, connected, authorized, tier-limited, state-limited, or temporarily inaccessible.

2. **Chessy — state continuity failed.** Conversational chess worked, but invoking the plugin mid-game did not preserve the board state established in chat. This tests chat → plugin state transfer, not chess capability generally.

3. **Replit — external state creation succeeded.** A request originating in chat produced observable state in an external build environment. Free-tier quota then became the next constraint.

4. **Runway — connection and entitlement differed.** Connection succeeded, while the attempted music-generation path encountered an account/tier limitation. Connectivity did not imply entitlement to every capability.

5. **Railway — connection/query succeeded.** The connected environment was queryable and reported no projects at test time. Create → deploy → persistence remained untested.

6. **Caveman/persona tooling — selection exposed; persistence untested.** Persona selection was available, but cross-message persistence was not established.

7. **Plugin inventory changes the terrain.** Adding tools during a conversation materially changed available experimental pathways. Capability is not adequately described by a single static inventory.

8. **Authorized external Mac shell pathway — demonstrated, then unavailable.** Earlier in the session an authorized external-computer pathway returned a harmless shell-test result. Later, that pathway was no longer exposed to the active toolset. Demonstrated capability did not imply continuous availability.

9. **Olympus Live — interface visible, runtime transport unavailable.** The connector interface was visible while the runtime/tunnel returned `tunnel_client_not_seen`. Startup/reconnect machinery appeared to exist, so the observation supports “transport down under tested conditions,” not “Olympus impossible to reach.”

## Main result
The useful experimental question is not merely **“Can Dio do X?”** It is:

> Under precisely what conditions can this instance, with this tool state, authorization, account tier, connectivity, and context, do X — and does the result reproduce?

**A door opening once is evidence of a door. It is not evidence that the door stays open.**
