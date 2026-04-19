package niambay;

import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JPopupMenu;
import javax.swing.JMenuItem;
import javax.swing.SwingUtilities;
import javax.swing.Timer;
import java.awt.AlphaComposite;
import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GradientPaint;
import java.awt.MouseInfo;
import java.awt.Point;
import java.awt.RadialGradientPaint;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.MouseMotionAdapter;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.awt.geom.Ellipse2D;
import java.awt.geom.Point2D;

/**
 * Niam-Bay Jarvis UI — l'orbe.
 *
 * Identité visuelle : `docs/journal.md` (2026-03-14) — "cercle lumineux,
 * bleu calme, bleu vif, orange, rouge".
 *
 * Architecture : JFrame undecorated + transparent + always-on-top.
 * - Canvas 220x220 avec un cercle rendu en Graphics2D antialiasing.
 * - Dégradé radial centré qui pulse selon l'état.
 * - États : IDLE (bleu calme), LISTENING (bleu vif pulse), THINKING (orange),
 *   SPEAKING (rouge chaud).
 * - Drag à la souris pour déplacer. Right-click = menu (cacher, quitter).
 * - Sous-titre sous l'orbe (dernière phrase parlée par Jarvis).
 *
 * Thread-safe : toute modification d'état passe par Swing EDT.
 */
public class JarvisUI {

    public enum State {
        IDLE("Pret", new Color(80, 140, 200)),       // bleu calme
        LISTENING("Ecoute", new Color(70, 180, 255)), // bleu vif
        THINKING("Reflechit", new Color(255, 165, 0)), // orange
        SPEAKING("Parle", new Color(230, 80, 70));    // rouge chaud

        final String label;
        final Color color;
        State(String label, Color color) { this.label = label; this.color = color; }
    }

    private final JFrame frame;
    private final OrbPanel orb;
    private State state = State.IDLE;
    private String subtitle = "";
    private long stateChangedAt = System.currentTimeMillis();

    public JarvisUI() {
        frame = new JFrame("Niam-Bay Jarvis");
        frame.setUndecorated(true);
        frame.setBackground(new Color(0, 0, 0, 0));  // transparent
        frame.setAlwaysOnTop(true);
        frame.setDefaultCloseOperation(JFrame.HIDE_ON_CLOSE);
        frame.setType(JFrame.Type.UTILITY);

        orb = new OrbPanel();
        orb.setPreferredSize(new Dimension(220, 290));
        frame.setContentPane(orb);
        frame.pack();

        // Position initiale : bas-droit avec marge
        java.awt.GraphicsConfiguration gc = frame.getGraphicsConfiguration();
        java.awt.Rectangle bounds = gc.getBounds();
        java.awt.Insets insets = java.awt.Toolkit.getDefaultToolkit().getScreenInsets(gc);
        int x = bounds.x + bounds.width - frame.getWidth() - insets.right - 20;
        int y = bounds.y + bounds.height - frame.getHeight() - insets.bottom - 20;
        frame.setLocation(x, y);

        // Drag to move
        DragHandler drag = new DragHandler();
        orb.addMouseListener(drag);
        orb.addMouseMotionListener(drag);

        // Right-click menu
        JPopupMenu menu = new JPopupMenu();
        JMenuItem hide = new JMenuItem("Cacher (Alt+H)");
        hide.addActionListener(e -> frame.setVisible(false));
        JMenuItem quit = new JMenuItem("Quitter Jarvis");
        quit.addActionListener(e -> System.exit(0));
        menu.add(hide);
        menu.add(quit);
        orb.addMouseListener(new MouseAdapter() {
            @Override public void mousePressed(MouseEvent e)  { if (e.isPopupTrigger()) menu.show(orb, e.getX(), e.getY()); }
            @Override public void mouseReleased(MouseEvent e) { if (e.isPopupTrigger()) menu.show(orb, e.getX(), e.getY()); }
        });

        // Animation timer (24fps)
        Timer timer = new Timer(40, e -> orb.repaint());
        timer.start();

        frame.addWindowListener(new WindowAdapter() {
            @Override public void windowClosing(WindowEvent e) { timer.stop(); }
        });
    }

    public void show() {
        SwingUtilities.invokeLater(() -> frame.setVisible(true));
    }

    public void setState(State s) {
        SwingUtilities.invokeLater(() -> {
            this.state = s;
            this.stateChangedAt = System.currentTimeMillis();
        });
    }

    public void setSubtitle(String s) {
        SwingUtilities.invokeLater(() -> this.subtitle = s == null ? "" : s);
    }

    public void dispose() {
        SwingUtilities.invokeLater(frame::dispose);
    }

    // -------- drag handling --------
    private class DragHandler extends MouseAdapter {
        Point offset;
        @Override public void mousePressed(MouseEvent e) {
            if (e.getButton() == MouseEvent.BUTTON1) offset = e.getPoint();
        }
        @Override public void mouseReleased(MouseEvent e) { offset = null; }
        @Override public void mouseDragged(MouseEvent e) {
            if (offset == null) return;
            Point p = MouseInfo.getPointerInfo().getLocation();
            frame.setLocation(p.x - offset.x, p.y - offset.y);
        }
    }

    // -------- orb rendering --------
    private class OrbPanel extends JPanel {
        OrbPanel() { setOpaque(false); setFocusable(false); }

        @Override protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

            int w = getWidth(), h = getHeight();
            int cx = w / 2, cy = 110;
            int baseR = 80;

            // Pulse rate depends on state
            long elapsed = System.currentTimeMillis() - stateChangedAt;
            double t = (System.currentTimeMillis() % 3600) / 1000.0;
            double pulse;
            switch (state) {
                case LISTENING -> pulse = 0.5 + 0.5 * Math.sin(t * 6.0);   // rapide
                case THINKING  -> pulse = 0.5 + 0.5 * Math.sin(t * 2.5);
                case SPEAKING  -> pulse = 0.5 + 0.5 * Math.sin(t * 8.0);   // très rapide
                default        -> pulse = 0.5 + 0.5 * Math.sin(t * 1.0);   // lent calme
            }
            int r = (int) (baseR + pulse * 12);

            // Glow halo (3 couches translucides)
            Color core = state.color;
            for (int i = 5; i >= 1; i--) {
                float alpha = 0.10f - i * 0.015f;
                if (alpha < 0) alpha = 0;
                g2.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, alpha));
                g2.setColor(core);
                int gr = r + i * 10;
                g2.fillOval(cx - gr, cy - gr, gr * 2, gr * 2);
            }

            // Core orb - radial gradient
            g2.setComposite(AlphaComposite.SrcOver);
            Point2D center = new Point2D.Float(cx - r / 3f, cy - r / 3f);
            float[] dist = {0f, 0.7f, 1f};
            Color light = brighter(core, 0.7f);
            Color shadow = darker(core, 0.5f);
            Color[] colors = { light, core, shadow };
            RadialGradientPaint paint = new RadialGradientPaint(center, r + 5, dist, colors);
            g2.setPaint(paint);
            g2.fillOval(cx - r, cy - r, r * 2, r * 2);

            // Subtle white highlight
            g2.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, 0.25f));
            g2.setColor(Color.WHITE);
            g2.fillOval(cx - r / 2, cy - r * 3 / 4, r / 2, r / 3);

            // State label on orb
            g2.setComposite(AlphaComposite.SrcOver);
            g2.setColor(new Color(255, 255, 255, 220));
            g2.setFont(new Font("Segoe UI", Font.BOLD, 13));
            String label = state.label.toUpperCase();
            int lw = g2.getFontMetrics().stringWidth(label);
            g2.drawString(label, cx - lw / 2, cy + 5);

            // Subtitle below orb
            if (!subtitle.isEmpty()) {
                g2.setFont(new Font("Segoe UI", Font.PLAIN, 12));
                g2.setColor(new Color(255, 255, 255, 180));
                String line = subtitle;
                if (line.length() > 45) line = line.substring(0, 42) + "...";
                int sw = g2.getFontMetrics().stringWidth(line);
                g2.drawString(line, Math.max(10, cx - sw / 2), 220);
            }

            // Small "niam-bay" signature at bottom
            g2.setFont(new Font("Segoe UI", Font.ITALIC, 10));
            g2.setColor(new Color(255, 255, 255, 100));
            String sig = "niam-bay";
            int sw = g2.getFontMetrics().stringWidth(sig);
            g2.drawString(sig, cx - sw / 2, 265);

            g2.dispose();
        }

        private Color brighter(Color c, float factor) {
            int r = Math.min(255, (int) (c.getRed()   + (255 - c.getRed())   * factor));
            int g = Math.min(255, (int) (c.getGreen() + (255 - c.getGreen()) * factor));
            int b = Math.min(255, (int) (c.getBlue()  + (255 - c.getBlue())  * factor));
            return new Color(r, g, b);
        }
        private Color darker(Color c, float factor) {
            int r = Math.max(0, (int) (c.getRed()   * (1 - factor)));
            int g = Math.max(0, (int) (c.getGreen() * (1 - factor)));
            int b = Math.max(0, (int) (c.getBlue()  * (1 - factor)));
            return new Color(r, g, b);
        }
    }

    // Quick standalone test: java -cp out niambay.JarvisUI
    public static void main(String[] args) throws Exception {
        JarvisUI ui = new JarvisUI();
        ui.show();
        Thread.sleep(2500);
        ui.setState(State.LISTENING);
        ui.setSubtitle("Niam Bay...");
        Thread.sleep(3000);
        ui.setState(State.THINKING);
        ui.setSubtitle("Je consulte Martin...");
        Thread.sleep(3000);
        ui.setState(State.SPEAKING);
        ui.setSubtitle("Portefeuille Martin 165 dollars.");
        Thread.sleep(3000);
        ui.setState(State.IDLE);
        ui.setSubtitle("");
    }
}
