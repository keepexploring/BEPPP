/**
 * QR Code generation and user card utilities
 */
import QRCode from 'qrcode'
import { jsPDF } from 'jspdf'

/**
 * Generate a short unique ID for a user
 * Format: BH-XXXX (BH = Battery Hub)
 */
export function generateUserShortId(userId) {
  // Create a short ID from user database ID
  const paddedId = String(userId).padStart(4, '0')
  return `BH-${paddedId}`
}

/**
 * Generate QR code as data URL
 */
export async function generateQRCode(data, options = {}) {
  const defaultOptions = {
    width: 300,
    margin: 2,
    color: {
      dark: '#000000',
      light: '#FFFFFF'
    },
    ...options
  }

  try {
    const dataUrl = await QRCode.toDataURL(data, defaultOptions)
    return dataUrl
  } catch (error) {
    console.error('Error generating QR code:', error)
    throw error
  }
}

/**
 * Generate user card PDF with QR code
 */
export async function generateUserCardPDF(user) {
  const pdf = new jsPDF({
    orientation: 'landscape',
    unit: 'mm',
    format: [85.6, 53.98] // Credit card size
  })

  // Generate QR code
  const shortId = user.short_id || generateUserShortId(user.id)
  const qrData = JSON.stringify({
    type: 'user',
    id: shortId,
    user_id: user.id,
    username: user.username
  })

  const qrCodeDataUrl = await generateQRCode(qrData, { width: 200 })

  // Card background
  pdf.setFillColor(25, 118, 210) // Primary blue
  pdf.rect(0, 0, 85.6, 53.98, 'F')

  // White card content area
  pdf.setFillColor(255, 255, 255)
  pdf.rect(3, 3, 79.6, 47.98, 'F')

  // Title
  pdf.setFontSize(14)
  pdf.setTextColor(25, 118, 210)
  pdf.setFont('helvetica', 'bold')
  pdf.text('Battery Hub', 42.8, 10, { align: 'center' })
  pdf.setFontSize(10)
  pdf.setFont('helvetica', 'normal')
  pdf.text('Rental Card', 42.8, 15, { align: 'center' })

  // User info
  pdf.setTextColor(0, 0, 0)
  pdf.setFontSize(11)
  pdf.setFont('helvetica', 'bold')
  pdf.text(user.full_name || user.username, 5, 23)

  pdf.setFontSize(9)
  pdf.setFont('helvetica', 'normal')
  pdf.text(`ID: ${shortId}`, 5, 28)
  pdf.text(`User: ${user.username}`, 5, 33)
  if (user.email) {
    pdf.text(user.email, 5, 38)
  }

  // QR Code (right side)
  pdf.addImage(qrCodeDataUrl, 'PNG', 55, 20, 25, 25)

  // Footer
  pdf.setFontSize(7)
  pdf.setTextColor(128, 128, 128)
  pdf.text('Scan QR code to start rental', 42.8, 48, { align: 'center' })

  return pdf
}

/**
 * Download user card as PDF
 */
export async function downloadUserCard(user) {
  const pdf = await generateUserCardPDF(user)
  const shortId = user.short_id || generateUserShortId(user.id)
  pdf.save(`battery-hub-card-${shortId}.pdf`)
}

/**
 * Generate multiple user cards on one page (for printing)
 */
export async function generateBulkUserCards(users) {
  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  })

  // A4 can fit approximately 6 cards (2x3 grid)
  const cardWidth = 85.6
  const cardHeight = 53.98
  const margin = 10
  const cardsPerRow = 2
  const cardsPerColumn = 3

  let cardCount = 0

  for (const user of users) {
    if (cardCount > 0 && cardCount % (cardsPerRow * cardsPerColumn) === 0) {
      pdf.addPage()
    }

    const row = Math.floor((cardCount % (cardsPerRow * cardsPerColumn)) / cardsPerRow)
    const col = cardCount % cardsPerRow

    const x = margin + (col * (cardWidth + margin))
    const y = margin + (row * (cardHeight + margin))

    // Generate individual card
    const userPdf = await generateUserCardPDF(user)
    const cardImage = userPdf.output('dataurlstring')

    pdf.addImage(cardImage, 'PNG', x, y, cardWidth, cardHeight)

    cardCount++
  }

  return pdf
}

/**
 * Parse QR code data
 */
export function parseQRData(qrString) {
  try {
    const data = JSON.parse(qrString)
    if (data.type === 'user') {
      return {
        type: 'user',
        shortId: data.id,
        userId: data.user_id,
        username: data.username
      }
    }
    return null
  } catch (error) {
    // If not JSON, might be just the short ID
    if (qrString.startsWith('BH-')) {
      return {
        type: 'user',
        shortId: qrString,
        userId: null,
        username: null
      }
    }
    return null
  }
}

export default {
  generateUserShortId,
  generateQRCode,
  generateUserCardPDF,
  downloadUserCard,
  generateBulkUserCards,
  parseQRData
}
