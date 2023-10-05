import React, { Component } from "react";
import { ContentElement } from "core_components/utils";

export function RenderPage(props) {
	const skill_props = props.skillState;

	return (
		<div className="v-aligned-container text-center">
            <ContentElement
				elementType={"TextFrame"}
				id={"title"}
				className={"col-12 h1"}
				text={skill_props.title}
				display={skill_props.display}
				duration={15000}
			/>
			<ContentElement
				elementType={"TextFrame"}
				id={"text"}
				className={"col-12 h3"}
				text={skill_props.text}
				display={skill_props.display}
				duration={15000}
			/>
		</div>
	);
}
