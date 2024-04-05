import React from "react";
import { ContentElement } from "CORE/utils";

function RenderPage(props) {
	const skill_props = props.skillState;
	console.log(skill_props)
	return (
		<div className="h-aligned-container text-center"
			 style={{justifyContent: "center",
				     alignItems: "center",
			 		 left: "1%",
			         right: "1%"}}>
			<ContentElement
				elementType="TextFrame"
				id="title"
				className="col-12 h2"
				text={skill_props["title"] || null}
				duration={15000}
			/>
			<ContentElement
				elementType="ImageFrame"
				id={"image"}
				className="col-12"
				src={skill_props["image"] || null}
				duration={15000}
			/>
			<ContentElement
				elementType="TextFrame"
				className="col-12 h4"
				text={skill_props["caption"] || null}
				duration={15000}
			/>
		</div>
	);
}

export default RenderPage