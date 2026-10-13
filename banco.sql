
DROP TABLE IF EXISTS logs;

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS categoria(
   id integer primary key autoincrement,
   nome varchar(50) not null,
   descricao text, 
   ativo boolean,
   imagem blob,
   img varchar(100)
);

CREATE TABLE IF NOT EXISTS produto(
   id integer primary key autoincrement,
   nome varchar(50) not null,
   preco float,
   ativo boolean, 
   imagem blob,
   img varchar(100),
   id_categoria int,
   foreign key ('id_categoria') references categoria('id')
);

CREATE TABLE IF NOT EXISTS usuario (
    id integer primary key AUTOINCREMENT,
    nome varchar(50) not null,
    senha varchar (50) not null,
    ativo boolean

);



