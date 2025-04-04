USE [CarPark]
GO
/****** Object:  Table [dbo].[Camera]    Script Date: 08/03/2025 10:11:08 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Camera](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[Name] [nvarchar](50) NULL,
	[BasePicture] [image] NULL,
	[ValVideo] [image] NULL,
	[ValLink] [nvarchar](max) NULL,
	[CheckInLoc] [int] NULL,
	[pt1x] [int] NULL,
	[pt1y] [int] NULL,
	[pt2x] [int] NULL,
	[pt2y] [int] NULL,
	[Manager] [nvarchar](50) NULL,
 CONSTRAINT [PK_Camera] PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[CameraHaveSlot]    Script Date: 08/03/2025 10:11:08 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[CameraHaveSlot](
	[Camera] [int] NOT NULL,
	[Slot] [int] NOT NULL,
	[pt1x] [int] NULL,
	[pt1y] [int] NULL,
	[pt2x] [int] NULL,
	[pt2y] [int] NULL,
 CONSTRAINT [PK_CameraHaveSlot] PRIMARY KEY CLUSTERED 
(
	[Camera] ASC,
	[Slot] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Manager]    Script Date: 08/03/2025 10:11:08 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Manager](
	[UserName] [nvarchar](50) NOT NULL,
	[Password] [nvarchar](50) NULL,
	[Email] [nvarchar](30) NULL,
	[PhoneNumber] [nvarchar](15) NULL,
 CONSTRAINT [PK_Manager] PRIMARY KEY CLUSTERED 
(
	[UserName] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Slot]    Script Date: 08/03/2025 10:11:08 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Slot](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[Name] [nvarchar](50) NULL,
	[Manager] [nvarchar](50) NULL,
 CONSTRAINT [PK_Slot] PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Ticket]    Script Date: 08/03/2025 10:11:08 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Ticket](
	[ID] [int] IDENTITY(1,1) NOT NULL,
	[Name] [nvarchar](50) NULL,
	[Manager] [nvarchar](50) NULL,
 CONSTRAINT [PK_Ticket] PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[TicketAllowSlot]    Script Date: 08/03/2025 10:11:08 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[TicketAllowSlot](
	[Ticket] [int] NOT NULL,
	[Slot] [int] NOT NULL,
 CONSTRAINT [PK_TicketAllowSlot] PRIMARY KEY CLUSTERED 
(
	[Ticket] ASC,
	[Slot] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
ALTER TABLE [dbo].[Camera]  WITH CHECK ADD  CONSTRAINT [FK_Camera_Manager] FOREIGN KEY([Manager])
REFERENCES [dbo].[Manager] ([UserName])
GO
ALTER TABLE [dbo].[Camera] CHECK CONSTRAINT [FK_Camera_Manager]
GO
ALTER TABLE [dbo].[CameraHaveSlot]  WITH CHECK ADD  CONSTRAINT [FK_CameraHaveSlot_Camera] FOREIGN KEY([Camera])
REFERENCES [dbo].[Camera] ([ID])
GO
ALTER TABLE [dbo].[CameraHaveSlot] CHECK CONSTRAINT [FK_CameraHaveSlot_Camera]
GO
ALTER TABLE [dbo].[CameraHaveSlot]  WITH CHECK ADD  CONSTRAINT [FK_CameraHaveSlot_Slot] FOREIGN KEY([Slot])
REFERENCES [dbo].[Slot] ([ID])
GO
ALTER TABLE [dbo].[CameraHaveSlot] CHECK CONSTRAINT [FK_CameraHaveSlot_Slot]
GO
ALTER TABLE [dbo].[Slot]  WITH CHECK ADD  CONSTRAINT [FK_Slot_Manager] FOREIGN KEY([Manager])
REFERENCES [dbo].[Manager] ([UserName])
GO
ALTER TABLE [dbo].[Slot] CHECK CONSTRAINT [FK_Slot_Manager]
GO
ALTER TABLE [dbo].[Ticket]  WITH CHECK ADD  CONSTRAINT [FK_Ticket_Manager] FOREIGN KEY([Manager])
REFERENCES [dbo].[Manager] ([UserName])
GO
ALTER TABLE [dbo].[Ticket] CHECK CONSTRAINT [FK_Ticket_Manager]
GO
ALTER TABLE [dbo].[TicketAllowSlot]  WITH CHECK ADD  CONSTRAINT [FK_TicketAllowSlot_Slot] FOREIGN KEY([Slot])
REFERENCES [dbo].[Slot] ([ID])
GO
ALTER TABLE [dbo].[TicketAllowSlot] CHECK CONSTRAINT [FK_TicketAllowSlot_Slot]
GO
ALTER TABLE [dbo].[TicketAllowSlot]  WITH CHECK ADD  CONSTRAINT [FK_TicketAllowSlot_Ticket] FOREIGN KEY([Ticket])
REFERENCES [dbo].[Ticket] ([ID])
GO
ALTER TABLE [dbo].[TicketAllowSlot] CHECK CONSTRAINT [FK_TicketAllowSlot_Ticket]
GO
