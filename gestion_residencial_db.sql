-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 28-08-2026 a las 19:18:53
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `gestion_residencial_db`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `adjuntos_reporte`
--

CREATE TABLE `adjuntos_reporte` (
  `Id_Adjunto` int(11) NOT NULL,
  `Id_Reporte_FK` int(11) DEFAULT NULL,
  `Nombre_Archivo` varchar(150) DEFAULT NULL,
  `Url_Archivo` varchar(255) DEFAULT NULL,
  `Tipo_Archivo` varchar(50) DEFAULT NULL,
  `Fecha_Subida` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pagos`
--

CREATE TABLE `pagos` (
  `Id_Pago` int(11) NOT NULL,
  `Id_Residente_FK` int(11) DEFAULT NULL,
  `Tipo_Pago` varchar(20) DEFAULT NULL,
  `Id_Reserva_FK` int(11) DEFAULT NULL,
  `Mes_Año` datetime DEFAULT NULL,
  `Valor` decimal(12,2) DEFAULT NULL,
  `Fecha_Vencimiento` date DEFAULT NULL,
  `Fecha_Pago` date DEFAULT NULL,
  `Metodo_Pago` varchar(30) DEFAULT NULL,
  `Comprobante_Url` varchar(255) DEFAULT NULL,
  `Estado` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `reportes`
--

CREATE TABLE `reportes` (
  `Id_Reportes` int(11) NOT NULL,
  `Id_Residente_FK` int(11) DEFAULT NULL,
  `Categoria` varchar(50) DEFAULT NULL,
  `Descripcion` text DEFAULT NULL,
  `Fecha_Reporte` datetime DEFAULT NULL,
  `Estado` varchar(20) DEFAULT NULL,
  `Asignado_a_FK` int(11) DEFAULT NULL,
  `Fecha_Resolucion` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `reservas`
--

CREATE TABLE `reservas` (
  `Id_Reservas` int(11) NOT NULL,
  `Id_Zona_FK` int(11) DEFAULT NULL,
  `Id_Unidad_FK` int(11) DEFAULT NULL,
  `Fecha_Reserva` datetime DEFAULT NULL,
  `Fecha_Inicio` datetime DEFAULT NULL,
  `Fecha_Fin` datetime DEFAULT NULL,
  `Estado` varchar(20) DEFAULT NULL,
  `Observaciones` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `residentes`
--

CREATE TABLE `residentes` (
  `Id_Residente` int(11) NOT NULL,
  `Tipo_Documento` varchar(100) DEFAULT NULL,
  `Num_Documento` varchar(100) DEFAULT NULL,
  `Nombres` varchar(255) DEFAULT NULL,
  `Apellidos` varchar(255) DEFAULT NULL,
  `Telefono` varchar(255) DEFAULT NULL,
  `Email` varchar(255) DEFAULT NULL,
  `Fecha_Registro` datetime DEFAULT NULL,
  `Estado` tinyint(1) DEFAULT NULL,
  `Id_Unidad_FK` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `residentes`
--

INSERT INTO `residentes` (`Id_Residente`, `Tipo_Documento`, `Num_Documento`, `Nombres`, `Apellidos`, `Telefono`, `Email`, `Fecha_Registro`, `Estado`, `Id_Unidad_FK`) VALUES
(1, 'CC', '123456', 'Juan', 'Pérez', '3001234567', 'juan@mail.com', '2026-08-28 12:02:30', 1, 1),
(2, 'CC', '123456', 'Juan', 'Pérez', '3001234567', 'juan@mail.com', '2026-08-28 12:03:12', 1, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `roles`
--

CREATE TABLE `roles` (
  `Id_Rol` int(11) NOT NULL,
  `Nombre` varchar(100) DEFAULT NULL,
  `Descripcion` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `roles`
--

INSERT INTO `roles` (`Id_Rol`, `Nombre`, `Descripcion`) VALUES
(1, 'Residente', 'Usuario con acceso de residente'),
(2, 'Residente', 'Usuario con acceso de residente'),
(3, 'Administrador', 'Usuario con acceso administrativo total'),
(4, 'Seguridad', 'Usuario del personal de seguridad/portería');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `unidades`
--

CREATE TABLE `unidades` (
  `Id_Unidad` int(11) NOT NULL,
  `Torre` varchar(10) DEFAULT NULL,
  `Apto` varchar(10) DEFAULT NULL,
  `Piso` int(11) DEFAULT NULL,
  `Area` decimal(8,2) DEFAULT NULL,
  `Id_Residente_FK` int(11) DEFAULT NULL,
  `Estado` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `unidades`
--

INSERT INTO `unidades` (`Id_Unidad`, `Torre`, `Apto`, `Piso`, `Area`, `Id_Residente_FK`, `Estado`) VALUES
(1, 'A', '101', 1, 65.50, 1, 1),
(2, 'A', '101', 1, 65.50, 1, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuario`
--

CREATE TABLE `usuario` (
  `Id_Usuario` int(11) NOT NULL,
  `Nombre` varchar(100) DEFAULT NULL,
  `Email` varchar(100) DEFAULT NULL,
  `Contraseña` varchar(255) DEFAULT NULL,
  `Id_Rol_FK` int(11) DEFAULT NULL,
  `Id_Residente_FK` int(11) DEFAULT NULL,
  `Estado` tinyint(1) DEFAULT NULL,
  `Fecha_creacion` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuario`
--

INSERT INTO `usuario` (`Id_Usuario`, `Nombre`, `Email`, `Contraseña`, `Id_Rol_FK`, `Id_Residente_FK`, `Estado`, `Fecha_creacion`) VALUES
(2, 'Juan Pérez', 'juan@mail.com', 'hash123', 1, 1, 1, '2026-08-28 12:03:03'),
(3, 'Juan Pérez', 'juan@mail.com', 'hash123', 1, 1, 1, '2026-08-28 12:03:12');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `vehiculos`
--

CREATE TABLE `vehiculos` (
  `Id_Vehiculo` int(11) NOT NULL,
  `Placa` varchar(10) DEFAULT NULL,
  `Marca` varchar(50) DEFAULT NULL,
  `Modelo` varchar(50) DEFAULT NULL,
  `Color` varchar(30) DEFAULT NULL,
  `Id_Residente_FK` int(11) DEFAULT NULL,
  `Tipo_Vehiculo` varchar(20) DEFAULT NULL,
  `Estado` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `visitantes`
--
