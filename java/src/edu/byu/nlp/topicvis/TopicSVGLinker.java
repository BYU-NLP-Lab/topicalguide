/**
 * The Topic Browser
 * Copyright 2010-2011 Brigham Young University
 * 
 * This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
 * 
 * The Topic Browser is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.
 * 
 * The Topic Browser is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
 * for more details.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * If you have inquiries regarding any further use of the Topic Browser, please
 * contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
 * Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.
 */
package edu.byu.nlp.topicvis;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.w3c.dom.bootstrap.DOMImplementationRegistry;
import org.w3c.dom.ls.DOMImplementationLS;
import org.w3c.dom.ls.LSSerializer;
import org.xml.sax.SAXException;


public class TopicSVGLinker {
	private static class Point {
		final double x;
		final double y;
		public Point(double x, double y) {
			this.x = x;
			this.y = y;
		}
		@Override
		public int hashCode() {
			final int prime = 31;
			int result = 1;
			long temp;
			temp = Double.doubleToLongBits(x);
			result = prime * result + (int) (temp ^ (temp >>> 32));
			temp = Double.doubleToLongBits(y);
			result = prime * result + (int) (temp ^ (temp >>> 32));
			return result;
		}
		@Override
		public boolean equals(Object obj) {
			if (this == obj)
				return true;
			if (obj == null)
				return false;
			if (getClass() != obj.getClass())
				return false;
			Point other = (Point) obj;
			if (Double.doubleToLongBits(x) != Double.doubleToLongBits(other.x))
				return false;
			if (Double.doubleToLongBits(y) != Double.doubleToLongBits(other.y))
				return false;
			return true;
		}


	}

	private final String datasetName;
	private final String analysisName;
	private final String highlightColor;
	private final Bijection<String> topicNameNumIdx;

	public TopicSVGLinker(String datasetName, String analysisName, final String highlightColor, Bijection<String> topicNameToTopicNum) {
		this.datasetName = datasetName;
		this.analysisName = analysisName;
		this.highlightColor = highlightColor;
		this.topicNameNumIdx = topicNameToTopicNum;
	}

	private String topicUrl(final int topicNum) {
		return "/datasets/" + datasetName + "/analyses/" + analysisName + "/topics/" + topicNum;
	}

	public void createLinkedSVG(final String srcSvgFilename, final String destSvgFilename, final int highlightTopicNum) {
		final File svgFile = new File(srcSvgFilename);
		final File linkedSvgFile = new File(destSvgFilename);
		final DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();

		try {
			final DocumentBuilder db = dbf.newDocumentBuilder();
			final Document doc = db.parse(svgFile);

			final NodeList labels = doc.getElementsByTagName("text");
			final Map<Point,String> topicLabelsByPosition = indexedLabels(labels);

			final NodeList Gs = doc.getElementsByTagName("g");
			for(int i = 0; i < Gs.getLength(); i++) {
				final Element g = (Element) Gs.item(i);

				if(g.getAttribute("id").equals("nodes")) {
					boolean foundHighlightNode = false;
					StringBuilder nodesFound = new StringBuilder();
					final NodeList children = g.getChildNodes();
					for(int j = 0; j < children.getLength(); j++) {
						final Node n = children.item(j);
						if(n instanceof Element) {
							final Element circle = (Element) n;
							final Point circlePoint = circleAsPoint(circle);
							final String topicName = topicLabelsByPosition.get(circlePoint);
							final int topicNum = topicNameNumIdx.indexOf(topicName);
							nodesFound.append(topicNum);
							nodesFound.append(' ');
							if(topicNum == highlightTopicNum) {
								//System.out.println("Prev color:" + circle.getAttribute("fill"));
								circle.removeAttribute("fill");
								circle.setAttribute("fill", highlightColor);
								foundHighlightNode = true;
							}
							final Element a = doc.createElement("a");
							a.setAttribute("xlink:href", topicUrl(topicNum));
							a.setAttribute("target", "_top");
							g.replaceChild(a, circle);
							a.appendChild(circle);
						}
					}

					if(!foundHighlightNode) {
						System.err.println("Couldn't find highlight node " + highlightTopicNum);
						System.err.println("\tsrc: " + srcSvgFilename);
						System.err.println("\tdest: " + destSvgFilename);
					}
				}

				if(g.getAttribute("id").equals("labels")) {
					final NodeList labelNodes = g.getChildNodes();
					for(int j = 0; j < labelNodes.getLength(); j++) {
						final Node n = labelNodes.item(j);
						if(n instanceof Element) {
							final Element labelElement = (Element) n;
							final String topicName = labelElement.getTextContent().trim();
							final int topicNum = topicNameNumIdx.indexOf(topicName);
							final Element a = doc.createElement("a");
							a.setAttribute("xlink:href", topicUrl(topicNum));
							a.setAttribute("target", "_top");
							g.replaceChild(a, labelElement);
							a.appendChild(labelElement);
						}
					}
				}
			}//end for

			DOMImplementationRegistry registry = DOMImplementationRegistry.newInstance();
			DOMImplementationLS impl = (DOMImplementationLS)registry.getDOMImplementation("LS");
			LSSerializer writer = impl.createLSSerializer();

			String str = writer.writeToString(doc);
			writeAsFile(str, linkedSvgFile);
		} catch (ParserConfigurationException e) {
			e.printStackTrace();
		} catch (SAXException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		} catch (ClassCastException e) {
			e.printStackTrace();
		} catch (ClassNotFoundException e) {
			e.printStackTrace();
		} catch (InstantiationException e) {
			e.printStackTrace();
		} catch (IllegalAccessException e) {
			e.printStackTrace();
		}
	}

	private static Point textAsPoint(final Element textElement) {
		return new Point(
				Double.parseDouble(textElement.getAttribute("x")),
				Double.parseDouble(textElement.getAttribute("y"))
		);
	}

	private static Point circleAsPoint(final Element circleElement) {
		return new Point(
				Double.parseDouble(circleElement.getAttribute("cx")),
				Double.parseDouble(circleElement.getAttribute("cy"))
		);
	}

	private static Map<Point,String> indexedLabels(final NodeList labels) {
		Map<Point,String> indexedLabels = new HashMap<Point,String>();
		for(int i = 0; i < labels.getLength(); i++) {
			final Element e = (Element) labels.item(i);
			final Point labelPosition = textAsPoint(e);
			indexedLabels.put(labelPosition, e.getTextContent().trim());
		}
		return indexedLabels;
	}

	private static void writeAsFile(final String s, final File f) {
		try {
			BufferedWriter w = new BufferedWriter(new FileWriter(f));
			w.append(s);
			w.flush();
			w.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}
