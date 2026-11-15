"""Movimento com colisão, usado pela jogadora e pelos inimigos terrestres.

A entidade precisa ter: rect, fx, fy (posição float), vy.
Plataformas 'unidirecionais' (as suspensas) só seguram quem cai por cima;
dá para pular por baixo delas e descer segurando S.
"""


def mover_corpo(ent, dx, dy, plataformas):
    # ---- eixo X (só plataformas sólidas)
    ent.fx += dx
    ent.rect.x = int(round(ent.fx))
    ent.bateu_parede = False
    if dx != 0:
        for p in plataformas:
            if p.unidirecional:
                continue
            if ent.rect.colliderect(p.rect):
                if dx > 0:
                    ent.rect.right = p.rect.left
                else:
                    ent.rect.left = p.rect.right
                ent.fx = float(ent.rect.x)
                ent.bateu_parede = True

    # ---- eixo Y
    base_antes = ent.rect.bottom
    ent.fy += dy
    ent.rect.y = int(round(ent.fy))
    ent.no_chao = False
    atravessar = getattr(ent, "atravessar", False)
    for p in plataformas:
        if not ent.rect.colliderect(p.rect):
            continue
        if p.unidirecional:
            if dy >= 0 and base_antes <= p.rect.top + 1 and not atravessar:
                ent.rect.bottom = p.rect.top
                ent.vy = 0
                ent.no_chao = True
                ent.fy = float(ent.rect.y)
        else:
            if dy > 0:
                ent.rect.bottom = p.rect.top
                ent.vy = 0
                ent.no_chao = True
                ent.fy = float(ent.rect.y)
            elif dy < 0:
                ent.rect.top = p.rect.bottom
                ent.vy = 0
                ent.fy = float(ent.rect.y)
