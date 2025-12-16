module rachadez

-- Assinaturas básicas
abstract sig Usuario {
    nome: one Nome,
    email: one Email,
    cpf: one CPF,
    telefone: lone Telefone
}

-- Tipos de usuário
sig Administrador extends Usuario {}
sig UsuarioComum extends Usuario {}

sig Nome, Email, Telefone, CPF {}

sig Arena {
    nome: one NomeArena,
    endereco: one Endereco,
    capacidade: lone Int
}

sig NomeArena, Endereco {}

-- Substitua sig Esporte por:
abstract sig NomeEsporte {}
one sig Society, Volei, Tenis, BeachTenis extends NomeEsporte {}

sig Esporte {
    nome: one NomeEsporte
}

sig Racha {
    criador: one Administrador,
    participantes: set Usuario,  -- Participantes podem ser qualquer Usuario
    esporte: one Esporte,
    local: one Arena,
    horario: one Horario,
    maxParticipantes: lone Int
}

sig Horario {
    inicio: one Tempo,
    fim: one Tempo
}

sig Tempo {
    dia: one Int,
    hora: one Int,
    minuto: one Int
}

-- Fatos (restrições)

-- Um usuário não pode ter o mesmo email ou CPF que outro
fact emailsCPFsUnicos {
    no disj u1, u2: Usuario | u1.email = u2.email
    no disj u1, u2: Usuario | u1.cpf = u2.cpf and u1.cpf != none
}

-- O horário de fim deve ser após o horário de início
fact horarioValido {
    all h: Horario | lt[h.inicio, h.fim]
}

-- Um usuário não pode participar de dois rachas no mesmo horário
fact semConflitoParticipacao {
    no disj r1, r2: Racha | 
        some u: Usuario | 
            u in r1.participantes and u in r2.participantes and
            conflitoHorario[r1.horario, r2.horario]
}

-- O criador NÃO é automaticamente participante (modificado)
fact criadorNaoAutomatico {
    all r: Racha | r.criador !in r.participantes
}

-- O número de participantes não pode exceder o máximo (se definido)
fact limiteParticipantes {
    all r: Racha | some r.maxParticipantes implies #r.participantes <= r.maxParticipantes
}

-- A capacidade da Arena deve ser sempre maior que zero
fact capacidadePositiva {
    all a: Arena | some a.capacidade implies a.capacidade > 0
}

-- Adicione ao sig Tempo
fact tempoValido {
    all t: Tempo | {
        t.dia >= 1 and t.dia <= 31
        t.hora >= 0 and t.hora <= 23
        t.minuto >= 0 and t.minuto <= 59
    }
}

fact nomesArenasUnicos {
    no disj a1, a2: Arena | a1.nome = a2.nome
}

fact capacidadeCompativel {
    all r: Racha | {
        some r.local.capacidade implies #r.participantes <= r.local.capacidade
    }
}

fact minimoParticipantes {
    all r: Racha | #r.participantes >= 1  -- Pelo menos 1 participante
}

-- Predicados e funções auxiliares
pred conflitoHorario[h1, h2: Horario] {
    not (lt[h1.fim, h2.inicio] or lt[h2.fim, h1.inicio])
}

pred lt[t1, t2: Tempo] {
    t1.dia = t2.dia and t1.hora = t2.hora implies t1.minuto < t2.minuto
    t1.dia = t2.dia implies t1.hora < t2.hora
    t1.dia < t2.dia
}

-- Operações (comandos)

-- Criar um novo racha (agora exige um Administrador)
pred criarRacha[c, c1: Racha, adm: Administrador, e: Esporte, l: Arena, h: Horario] {
    c1 not in Racha
    c1.criador = adm
    c1.esporte = e
    c1.local = l
    c1.horario = h
    no c1.participantes  -- Admin não é mais automaticamente adicionado
    no c1.maxParticipantes
    Racha' = Racha + c1
}

-- Adicionar participante a um racha (qualquer usuário pode ser adicionado)
pred adicionarParticipante[r, r1: Racha, u: Usuario] {
    u not in r.participantes
    some r.maxParticipantes implies #r.participantes < r.maxParticipantes
    r1.participantes = r.participantes + u
    r1.esporte = r.esporte
    r1.local = r.local
    r1.horario = r.horario
    r1.maxParticipantes = r.maxParticipantes
    Racha' = Racha - r + r1
}

-- Remover participante de um racha (exceto o criador se estiver participando)
pred removerParticipante[r, r1: Racha, u: Usuario] {
    u in r.participantes
    u != r.criador  -- o criador (Administrador) não pode ser removido se estiver participando
    r1.participantes = r.participantes - u
    r1.esporte = r.esporte
    r1.local = r.local
    r1.horario = r.horario
    r1.maxParticipantes = r.maxParticipantes
    Racha' = Racha - r + r1
}

pred show[]{}
run show for 10
