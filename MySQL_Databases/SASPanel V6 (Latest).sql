-- phpMyAdmin SQL Dump
-- version 5.0.2
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Mar 27, 2022 at 10:16 AM
-- Server version: 5.7.31
-- PHP Version: 7.3.21

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `saspanel`
--

-- --------------------------------------------------------

--
-- Table structure for table `administrator`
--

DROP TABLE IF EXISTS `administrator`;
CREATE TABLE IF NOT EXISTS `administrator` (
  `Admin_id` int(11) NOT NULL AUTO_INCREMENT,
  `Admin_Name` varchar(100) NOT NULL,
  `Admin_Username` varchar(100) NOT NULL,
  `Admin_Password` varchar(150) NOT NULL,
  `Admin_Email` varchar(150) NOT NULL,
  `Is_Active` int(11) NOT NULL DEFAULT '1',
  `Admin_type` varchar(20) NOT NULL,
  `Reg_Date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Admin_id`),
  UNIQUE KEY `Admin_Username` (`Admin_Username`),
  UNIQUE KEY `Admin_Email` (`Admin_Email`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `administrator`
--

INSERT INTO `administrator` (`Admin_id`, `Admin_Name`, `Admin_Username`, `Admin_Password`, `Admin_Email`, `Is_Active`, `Admin_type`, `Reg_Date`) VALUES
(1, 'Test Admin', 'TestAdmin', '202cb962ac59075b964b07152d234b70', 'admin@admin.com', 1, '1', '2022-01-17 19:30:07');

-- --------------------------------------------------------

--
-- Table structure for table `domains`
--

DROP TABLE IF EXISTS `domains`;
CREATE TABLE IF NOT EXISTS `domains` (
  `Domain_Id` int(11) NOT NULL AUTO_INCREMENT,
  `Domain_Name` varchar(200) NOT NULL,
  `User_id` int(11) NOT NULL,
  `Domain_Suspended` int(11) NOT NULL,
  `Is_Deleted` int(11) NOT NULL,
  PRIMARY KEY (`Domain_Id`),
  UNIQUE KEY `Domain_Name` (`Domain_Name`)
) ENGINE=MyISAM AUTO_INCREMENT=9 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `domains`
--

INSERT INTO `domains` (`Domain_Id`, `Domain_Name`, `User_id`, `Domain_Suspended`, `Is_Deleted`) VALUES
(1, 'test.com', 2, 0, 0),
(2, 'testdomain.com', 1, 0, 0),
(8, 'testdomain1.com', 1, 0, 1),
(6, 'devil.com', 1, 0, 1),
(7, 'hello.com', 1, 0, 0);

-- --------------------------------------------------------

--
-- Table structure for table `ftp_accounts`
--

DROP TABLE IF EXISTS `ftp_accounts`;
CREATE TABLE IF NOT EXISTS `ftp_accounts` (
  `Account_Id` int(11) NOT NULL AUTO_INCREMENT,
  `User_id` int(11) NOT NULL,
  `Directory` varchar(250) NOT NULL,
  `FTP_Username` varchar(100) NOT NULL,
  `FTP_Password` varchar(200) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`Account_Id`),
  UNIQUE KEY `FTP_Username` (`FTP_Username`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `ftp_accounts`
--

INSERT INTO `ftp_accounts` (`Account_Id`, `User_id`, `Directory`, `FTP_Username`, `FTP_Password`, `Is_Active`) VALUES
(1, 2, '/home/username/public_html', 'haxor', 'haxor', 1),
(2, 2, 'test', 'test', 'VGVzdFBhc3M=', 1),
(3, 11, '/home/username/public_html', 'ftp_account', 'YXNkZjEyMzQ=', 1),
(4, 1, '/home/username/public_html', 'TestUser', 'VGVzdFVzZXI=', 1);

-- --------------------------------------------------------

--
-- Table structure for table `mail_accounts`
--

DROP TABLE IF EXISTS `mail_accounts`;
CREATE TABLE IF NOT EXISTS `mail_accounts` (
  `Mail_Id` int(11) NOT NULL AUTO_INCREMENT,
  `Domain_Id` int(11) NOT NULL,
  `User_id` int(11) NOT NULL,
  `Mail_Address` varchar(100) NOT NULL,
  `Mail_Pass` varchar(100) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`Mail_Id`),
  UNIQUE KEY `Mail_Address` (`Mail_Address`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `mail_accounts`
--

INSERT INTO `mail_accounts` (`Mail_Id`, `Domain_Id`, `User_id`, `Mail_Address`, `Mail_Pass`, `Is_Active`) VALUES
(1, 1, 1, 'support@domain.com', 'AZ=', 0),
(2, 2, 1, 'testAccount@testdomain.com', 'MTIzNDU2', 0),
(3, 2, 1, 'ew@testdomain.com', 'TmV3UGFzcw==', 1),
(4, 7, 1, 'testAccount@hello.com', 'YWRkRW1haWw=', 1),
(5, 2, 1, 'dsdasdasdsadasd@testdomain.com', 'VGVzdA==', 1);

-- --------------------------------------------------------

--
-- Table structure for table `msqldatabases`
--

DROP TABLE IF EXISTS `msqldatabases`;
CREATE TABLE IF NOT EXISTS `msqldatabases` (
  `DB_ID` int(11) NOT NULL AUTO_INCREMENT,
  `DbName` varchar(50) NOT NULL,
  `User_id` int(11) NOT NULL,
  `DbUser_ID` int(11) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`DB_ID`),
  UNIQUE KEY `DbName` (`DbName`)
) ENGINE=MyISAM AUTO_INCREMENT=13 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `msqldatabases`
--

INSERT INTO `msqldatabases` (`DB_ID`, `DbName`, `User_id`, `DbUser_ID`, `Is_Active`) VALUES
(12, 'a231', 1, 7, 1),
(11, 'TESTCFD', 11, 4, 1);

-- --------------------------------------------------------

--
-- Table structure for table `mysqldbusers`
--

DROP TABLE IF EXISTS `mysqldbusers`;
CREATE TABLE IF NOT EXISTS `mysqldbusers` (
  `DbUser_ID` int(11) NOT NULL AUTO_INCREMENT,
  `DbUsername` varchar(30) NOT NULL,
  `DbPassword` varchar(150) NOT NULL,
  `User_id` int(11) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`DbUser_ID`),
  UNIQUE KEY `DbUsername` (`DbUsername`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `mysqldbusers`
--

INSERT INTO `mysqldbusers` (`DbUser_ID`, `DbUsername`, `DbPassword`, `User_id`, `Is_Active`) VALUES
(4, 'zayazaya223', 'dGVzdHBhc3M=', 11, 1),
(5, 'aArsalan7', '$S4uZ^Z2', 12, 1),
(6, 'dProduct834', 'SDcrZ2RLeVs=', 13, 1),
(7, 'testdatabase', 'dGVzdA==', 1, 1);

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
CREATE TABLE IF NOT EXISTS `notifications` (
  `Notification_ID` int(11) NOT NULL,
  `Admin_id` int(11) NOT NULL,
  `Notification_Title` varchar(50) NOT NULL,
  `Notification_Message` varchar(300) NOT NULL,
  `Notification_Date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Is_Active` int(11) NOT NULL,
  `User_id` int(11) NOT NULL,
  PRIMARY KEY (`Notification_ID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `packages`
--

DROP TABLE IF EXISTS `packages`;
CREATE TABLE IF NOT EXISTS `packages` (
  `Package_Id` int(11) NOT NULL AUTO_INCREMENT,
  `Package_Name` varchar(100) NOT NULL,
  `Admin_id` int(11) NOT NULL,
  `Limit_FTP` int(11) NOT NULL,
  `Limit_Mails` int(11) NOT NULL,
  `Limit_Domains` int(11) NOT NULL,
  `CGI_ACCESS` int(11) NOT NULL,
  `Limit_DB` int(11) NOT NULL,
  `Sub_Domains` int(11) NOT NULL,
  `Storage_Limit` int(11) NOT NULL,
  `Is_Active` int(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`Package_Id`)
) ENGINE=MyISAM AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `packages`
--

INSERT INTO `packages` (`Package_Id`, `Package_Name`, `Admin_id`, `Limit_FTP`, `Limit_Mails`, `Limit_Domains`, `CGI_ACCESS`, `Limit_DB`, `Sub_Domains`, `Storage_Limit`, `Is_Active`) VALUES
(1, 'Demo_Account', 1, 1, 55, 5, 0, 52, 55, 156, 0),
(8, 'Test', 1, 5, 5, 5, 1, 5, 5, 5, 1),
(9, 'Ultimate', 1, 100, 100, 550, 1, 100, 100, 10, 1),
(10, 'Samar', 1, 0, 0, 500, 1, 0, 0, 0, 1);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `User_id` int(11) NOT NULL AUTO_INCREMENT,
  `servUser` varchar(40) NOT NULL,
  `User_email` varchar(150) NOT NULL,
  `User_Password` varchar(200) NOT NULL,
  `User_Name` varchar(100) NOT NULL,
  `UserResetToken` varchar(200) NOT NULL,
  `Token_Expiry` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Admin_id` int(11) NOT NULL,
  `Package_id` int(11) NOT NULL,
  `Is_Deleted` int(11) NOT NULL,
  `User_Reg_Date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`User_id`),
  UNIQUE KEY `User_email` (`User_email`)
) ENGINE=MyISAM AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`User_id`, `servUser`, `User_email`, `User_Password`, `User_Name`, `UserResetToken`, `Token_Expiry`, `Admin_id`, `Package_id`, `Is_Deleted`, `User_Reg_Date`) VALUES
(1, 'test1', 'test@test.com', '202cb962ac59075b964b07152d234b70', 'Test Account', '', '2022-01-17 19:28:59', 1, 1, 0, '2022-01-17 19:28:59'),
(13, 'dProduct818', 'ProductAdd@ProductAdd.com', '5255c0120430256776b55522f4c998d8', 'ProductAdd', '', '2022-03-20 12:11:57', 1, 8, 0, '2022-03-20 12:11:57'),
(12, 'aArsalan85', 'Arsalan@Arsalan.com', '8d55950739cfafb232f90aef3970a41a', 'Arsalan', '', '2022-03-20 12:06:46', 1, 8, 0, '2022-03-20 12:06:46'),
(11, 'zayazaya4', 'ayaz@ayaz.com', '29d867687b8d0b64f663f8e7a39b8df1', 'Ayaz', '', '2022-03-20 08:19:58', 1, 8, 0, '2022-03-20 08:19:58');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
