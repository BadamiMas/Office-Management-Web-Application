-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Oct 23, 2025 at 07:25 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `icsp`
--

-- --------------------------------------------------------

--
-- Table structure for table `attendance`
--

CREATE TABLE `attendance` (
  `id` int(11) NOT NULL,
  `user_name` varchar(100) NOT NULL,
  `login_time` datetime DEFAULT NULL,
  `logout_time` datetime DEFAULT NULL,
  `date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `cash_flow`
--

CREATE TABLE `cash_flow` (
  `id` int(11) NOT NULL,
  `flow_date` date NOT NULL,
  `cash_in` decimal(10,2) DEFAULT NULL,
  `cash_out` decimal(10,2) DEFAULT NULL,
  `name` char(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `cash_flow`
--

INSERT INTO `cash_flow` (`id`, `flow_date`, `cash_in`, `cash_out`, `name`) VALUES
(1, '2025-10-16', 1000.50, 0.00, 'Novatech Systems'),
(2, '2025-06-24', 0.00, 3759.40, 'Salaries'),
(3, '2025-10-20', 0.00, 670.59, 'Salaries'),
(4, '2025-05-12', 950.70, 0.00, 'Creston Management'),
(5, '2025-10-16', 746.80, 0.00, 'RevolvEco Group'),
(6, '2025-05-26', 8543.30, 523.38, 'HydraCore Renewables'),
(7, '2025-08-15', 955.00, 297.80, 'Novatech Systems'),
(8, '2025-08-09', 1369.00, NULL, 'Vitalis Dynamics'),
(9, '2025-07-05', 5089.60, NULL, 'Creston Management'),
(10, '2025-06-27', 2359.81, NULL, 'Parallax Investments'),
(11, '2025-07-25', NULL, 1967.00, 'Salaries');

-- --------------------------------------------------------

--
-- Table structure for table `employees`
--

CREATE TABLE `employees` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `role` varchar(100) NOT NULL,
  `date_hired` date NOT NULL,
  `number` varchar(20) NOT NULL,
  `age` int(11) NOT NULL,
  `city` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `employees`
--

INSERT INTO `employees` (`id`, `name`, `role`, `date_hired`, `number`, `age`, `city`, `email`) VALUES
(1, 'John Doe', 'IT', '2025-10-12', '12345678', 25, 'New York City', 'johndoe@sc.com'),
(2, 'Edward Buck', 'Supervisor', '2025-09-09', '89748651', 23, 'London', 'edwardbuck@sc.com'),
(3, 'Jasmine Tan', 'IT Assistant', '2025-10-09', '56483264', 23, 'Beijing', 'jasminetan@sc.com'),
(4, 'Kayla Moon', 'HR', '2025-02-12', '48635266', 46, 'Edinburgh', 'kaylamoon@sc.com'),
(5, 'Bobby Deol', 'Manager', '2025-06-14', '78642315', 43, 'Mumbai', 'bobbydeol@sc.com'),
(6, 'Maryam Ali', 'HR Assistant', '2025-07-07', '35648189', 35, 'Dubai', 'maryamali@sc.com'),
(8, 'Ahmed Karim', 'Manager Assistant', '2025-05-11', '84563247', 31, 'Singapore', 'ahmedkarim@sc.com'),
(9, 'Yusuf Ali', 'HR', '2025-05-12', '54646689', 54, 'Dubai', 'yusufali@sc.com'),
(10, 'Dheepa Nguyen', 'Sub Supervisor', '2025-05-13', '46516697', 35, 'Hanoi', 'dheepanguyen@sc.com'),
(11, 'Arya Molins', 'Supervisor', '2025-01-16', '78351696', 42, 'Perth', 'aryamolins@sc.com'),
(12, 'Ryan Lim', 'Head', '2025-10-21', '78561996', 50, 'Singapore', 'ryanlim@sc.com'),
(13, 'Nuz Hawkin', 'Accountant', '2025-10-01', '87866541', 37, 'Singapore', 'nuzhawkin@sc.com');

-- --------------------------------------------------------

--
-- Table structure for table `tasks`
--

CREATE TABLE `tasks` (
  `id` int(11) NOT NULL,
  `user_name` varchar(100) NOT NULL,
  `task_text` varchar(255) NOT NULL,
  `status` enum('pending','completed') DEFAULT 'pending',
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('Head','HR','Accountant') NOT NULL,
  `face_encode` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `password`, `role`, `face_encode`) VALUES
(3, 'me', '$2b$12$sjLhMopmTojkL2c5GX6.tuRFOXDh/N9Vgusak3SMGRICwpXMOeTuy', 'Head', 'AAAA4Hv/ur8AAAAAiHOyPwAAAEDBSqk/AAAA4HINs78AAACA1wqsvwAAACDq/Kq/AAAAwLxNmr8AAADAb4q5vwAAAMC4Is4/AAAAoJO7xb8AAAAAJGLJPwAAAEDsYKS/AAAAgHSZzb8AAAAAp6R4vwAAAICV6aS/AAAA4D58wz8AAABgre/BvwAAAKDUIcS/AAAA4J9Grr8AAABgHiKzvwAAAGCOqZM/AAAAQDJzSr8AAACgPlWrPwAAAKA5fLI/AAAAgOpawL8AAADA80nVvwAAACByubW/AAAAQDvkub8AAAAgbKufvwAAAADZMra/AAAAABL7Xb8AAABAbLDBPwAAAGD+q8i/AAAAAD8uir8AAAAAlNByPwAAAIBkvMA/AAAAAEYakL8AAABAktOUvwAAAKC6lc4/AAAAQDSEkr8AAACg6W3NvwAAAGDcqrO/AAAAIGpnmz8AAABgfRzJPwAAACCdc8U/AAAAAF5GmT8AAAAAl9KJPwAAAKCoqby/AAAAIAHPtD8AAADgdubJvwAAAMCetZk/AAAAwI40wj8AAAAgRZ+1PwAAAABzon4/AAAAALcWsT8AAAAgAbLAvwAAAAA+pqk/AAAAgDhAmD8AAADgc6rEvwAAAODaBLC/AAAAwMBOrD8AAACAg53BvwAAAGC8rqa/AAAAIHdSlb8AAABgS5jNPwAAACA9x7o/AAAAAG0Nsb8AAADAMae5vwAAAGArnMc/AAAA4Eh3yr8AAAAgMwywvwAAAADA47I/AAAAYBGotL8AAABghdTGvwAAAOCXUtO/AAAAwJcum78AAACgnZPZPwAAAGA+UsE/AAAAIKMavr8AAADgtunDPwAAAKAPeYO/AAAAgGUVrb8AAACg5qCzPwAAAGDDicE/AAAAQI7RxL8AAAAgTBq+PwAAAAAv366/AAAAwJNYsT8AAAAAKbDJPwAAAAApKn+/AAAAoCF2rr8AAAAA70vAPwAAAOCQJ6O/AAAAIH7CtD8AAABAvmy4PwAAAOCJB5y/AAAAoJS/ob8AAADgkP6hvwAAAEBhOsW/AAAAANDtIb8AAACAOP+hPwAAAMDk9pm/AAAAgI/zpL8AAABAmMixPwAAAIASxMa/AAAAAEtRsz8AAAAg31qqvwAAAMBdLLu/AAAAAEmIrr8AAACA/lugPwAAAOAZqbq/AAAAQJ5dqr8AAABAj2/CPwAAAICmOM6/AAAAwEHJvj8AAABAAznBPwAAAMA2L6e/AAAA4KYGxz8AAABgUGO/PwAAAACIfbg/AAAAwHOndr8AAADAJ8mSvwAAAABCmMW/AAAAgNrssL8AAACAwqfCPwAAAIC7nHm/AAAAgMcoxj8AAACA1sZZvw=='),
(14, 'prof', '$2b$12$loOvZLGPA2j1CqgkWNFbMesRb1T0CbDLBAjwm/ywI57fm0I9WfiU6', 'HR', 'AAAAAGexvb8AAABg5rO+PwAAAKDqeLc/AAAAYE18qj8AAADAXhKFvwAAAKDVtKy/AAAAoM1uqT8AAADgWLDEvwAAAKAPZLA/AAAAwEEzi78AAAAAUQbVPwAAAMC3mLm/AAAAACPwzr8AAABg1hrHvwAAAOC8Bnm/AAAA4KQuxz8AAAAgTKXAvwAAAMBoMcO/AAAAQH75ub8AAABAeT2rvwAAAKD6wZs/AAAAgL8Vo78AAACAoT+nPwAAAOBVHpk/AAAAAAZKZT8AAABgIOrYvwAAAEC8ZLm/AAAAQN6Hw78AAACArF6zPwAAAID5lXa/AAAA4EKcj78AAAAgrjM1vwAAAGA218q/AAAAYOAQub8AAAAg0VSjPwAAAMCUD7g/AAAAoBklYz8AAABgJ5iRPwAAAACRAMQ/AAAAQJ2Zs78AAADAiD2/vwAAAICstJ0/AAAAoEuWrD8AAABAIbfKPwAAAMAjTMM/AAAAANj9vz8AAADAqjyrPwAAAAC5OrG/AAAAACrbg78AAADA+bbEvwAAAEDkWJk/AAAAwLF8wD8AAACApTO6PwAAACClj7I/AAAAQEsrd78AAACA9aG/vwAAAMBv4qm/AAAA4CWJsT8AAAAgeYjAvwAAAOD5OZA/AAAAoK6Doj8AAADA8e69vwAAAKDPPrO/AAAAQFpIrL8AAAAgYXrOPwAAAMCUAKI/AAAAgEWftb8AAABgYrzEvwAAAIArhcI/AAAAgGSPxL8AAACAwMStvwAAAMBoZaA/AAAAYG3TwL8AAABgxw+1vwAAAGBZI9K/AAAAICxQuT8AAACAHq7cPwAAAEARsZc/AAAAQNRhw78AAACANZioPwAAAADYNsS/AAAAQOVMaD8AAADgsapjvwAAAGAfj4E/AAAAALeogz8AAABAbLKbvwAAAIDyrMW/AAAA4Gxdpb8AAADgTsPDPwAAAMDseMC/AAAAwCTupT8AAABgDOnCPwAAAEAf1bm/AAAAwPkgsD8AAAAAVRWIvwAAAIAcFYc/AAAAIJE9rb8AAADgJh2pPwAAAEAS5LG/AAAAQA9Jsr8AAABAuvKXPwAAAEC6jqe/AAAAICYLmD8AAACA04SGPwAAAOD/zMe/AAAAYERvnj8AAABgw0ahvwAAAIBQApA/AAAA4CyNrD8AAABA2FWiPwAAAEDGDrG/AAAAYMjEuL8AAACgcgXEPwAAAMDDH8+/AAAAAFGQ0D8AAADApavPPwAAACChVJi/AAAAwAuLvD8AAAAAFYu1PwAAAKDF8MA/AAAA4CNUlr8AAADAT8SDvwAAAIADxsa/AAAAAB9dtb8AAAAgxASsPwAAACCamZ8/AAAAwFqsk78AAAAgw1OTPw=='),
(15, 'nuz', '$2b$12$rT4/MJRFyfcyrKrXhIEjgeBL0LgIH11RzPfZCfXJPq.jv6trt9WaW', 'Accountant', 'AAAAoIarvb8AAACAo2RsPwAAAOAFKpm/AAAA4Ogpw78AAADgLuK8vwAAAECdKLW/AAAAQIuJiT8AAADgdYXBvwAAAEBqWMI/AAAAoNY/wL8AAAAALknJPwAAAGD3tb2/AAAAALcDzb8AAAAAXBSnvwAAAGBNQqm/AAAAYN+axj8AAACAL9PMvwAAAKClE8W/AAAAAFEDZz8AAABAmUaevwAAACAPVag/AAAA4IYPlz8AAAAAeTuMvwAAAICvabQ/AAAAIG5lv78AAACgVl7UvwAAAACq1bm/AAAAoAQGtb8AAADgNa+YvwAAAECn05O/AAAAwPonlz8AAADgMoy+PwAAAKB1Uc2/AAAAgBozn78AAACAotWhPwAAAIDwk7o/AAAAAHpMgz8AAADgbOizvwAAACAKO8U/AAAAQBqMfT8AAABA1IrQvwAAAGAH2LO/AAAAAFSiwT8AAACgxBbMPwAAAGAyKLs/AAAAAL0wmL8AAACAjjOgvwAAAOA9NK+/AAAAANcXqj8AAACArV7IvwAAAADjxYK/AAAA4PTwvz8AAADgGh22PwAAAAAyjpw/AAAAgK/emL8AAADAWs69vwAAAMBQZak/AAAA4Irauz8AAACg/HDFvwAAAOD/e6q/AAAAoNCCtj8AAAAgbQ2xvwAAAOBxw6e/AAAAAIC1sr8AAAAA5NHRPwAAAGBtPrY/AAAAIEKYwr8AAAAALnu7vwAAAIAhOsM/AAAAQNkOwr8AAAAAhAu9vwAAAIBDvIw/AAAAwMlxw78AAAAgaMPDvwAAAMC8DdS/AAAAgCn0h78AAACgMhjWPwAAAMAFXbA/AAAAYKx/wb8AAAAAGJ22PwAAAEDBJaq/AAAAQH1/mT8AAADAYly7PwAAAICBbsM/AAAAYGnckr8AAAAgAdmzPwAAAGDv3Ky/AAAAAMxamT8AAABg4g3IPwAAAKAk06u/AAAAwBNwpb8AAAAAn1XDPwAAAGC5JJ+/AAAAgHtzrT8AAABgwRqlPwAAAIDHNZs/AAAAABgEnb8AAAAAJwWXvwAAAGCSCMK/AAAAwJ3anj8AAAAAotqdPwAAAMANzpW/AAAAwNhQqb8AAADgNvfFPwAAAEByPcS/AAAAYBoQtj8AAADgJHilPwAAAIA3JrG/AAAAgOA7ar8AAABA4SuZPwAAAKCn76G/AAAAgBqfvL8AAABARiewPwAAAIAJZ8y/AAAAANz2xT8AAABASDjFPwAAAMBrtYK/AAAAYGQDwj8AAABAfdywPwAAAIDMHqs/AAAAgCzXmr8AAACAEqyIvwAAAKByLMm/AAAA4FVGrb8AAAAA/P6/PwAAAIDin6G/AAAAwFKhtD8AAABAkUmUvw==');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `attendance`
--
ALTER TABLE `attendance`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `cash_flow`
--
ALTER TABLE `cash_flow`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `employees`
--
ALTER TABLE `employees`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tasks`
--
ALTER TABLE `tasks`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `attendance`
--
ALTER TABLE `attendance`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `cash_flow`
--
ALTER TABLE `cash_flow`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `employees`
--
ALTER TABLE `employees`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `tasks`
--
ALTER TABLE `tasks`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
